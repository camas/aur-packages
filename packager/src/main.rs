use clap::{clap_app, crate_authors, crate_version, AppSettings};
use packager_lib::{run_command, run_command_no_capture, Package, PackageManager};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

const DOCKER_TAG: &str = "camas/aur-packages";

fn main() {
    // Parse command line arguments
    let app = clap_app!(("packager") =>
        (version: crate_version!())
        (author: crate_authors!())
        (about: "AUR Package Manager")
        (setting: AppSettings::ArgRequiredElseHelp)
        (@arg directory: -d --("base-dir") +takes_value "Set base dir to use")
        (@subcommand list =>
            (about: "List packages")
        )
        (@subcommand header =>
            (about: "Show header")
        )
        (@subcommand test =>
            (about: "Test a package")
            (@arg use_shell: -s --shell "Enter into a shell after testing")
            (@arg skip_build: --("skip-build") "Skip building the docker container")
            (@arg skip_makepkg: --("skip-makepkg") "Skip building and installing the package in docker")
            (@arg package: +required "The package to test")
        )
        (@subcommand build =>
            (about: "Build the docker image")
            (@arg full_build: -f --full "Build the image fully")
        )
    );
    let matches = app.get_matches();

    // Start package manager
    let base_dir = if let Some(d) = matches.value_of("directory") {
        PathBuf::from(d)
    } else {
        PathBuf::from("./")
    };
    let package_dir = base_dir.join("packages");
    let manager = PackageManager::from_dir(&package_dir);

    // Handle sub command
    if matches.subcommand_matches("list").is_some() {
        list_packages(manager);
    } else if matches.subcommand_matches("header").is_some() {
        print_header(manager);
    } else if let Some(matches) = matches.subcommand_matches("test") {
        let package_name = matches.value_of("package").expect("Package not specified");
        let package = manager
            .packages()
            .iter()
            .find(|package| package.name() == package_name)
            .expect("Package not found");
        let use_shell = matches.is_present("use_shell");
        let skip_makepkg = matches.is_present("skip_makepkg");
        let skip_build = matches.is_present("skip_build");
        test_package(package_dir, package, use_shell, skip_makepkg, skip_build);
    } else if let Some(matches) = matches.subcommand_matches("build") {
        let full_build = matches.is_present("full_build");
        build_image(base_dir, full_build);
    } else {
        panic!();
    }
}

/// Display a list of all packages
fn list_packages(manager: PackageManager) {
    let packages = manager.packages();
    println!("{} packages:", packages.len());
    for package in packages {
        println!("{:<32}    VERSIONTODO-RELEASETODO", package.name());
    }
}

/// Print a formatted header
fn print_header(manager: PackageManager) {
    // Get git info
    let git_branch_output = run_command("git", &["rev-parse", "--abbrev-ref", "HEAD"]);
    let git_branch = git_branch_output.lines().next().expect("No output");
    let git_hash_output = run_command("git", &["rev-list", "-n", "1", "HEAD"]);
    let git_hash = git_hash_output.lines().next().expect("No output");
    let git_commits_output = run_command("git", &["rev-list", "--count", "HEAD"]);
    let git_commits = git_commits_output.lines().next().expect("No output");
    let git_string = format!(
        "{} | {} | {} commits",
        git_branch,
        &git_hash[..8],
        git_commits
    );

    // Get and format package names
    let mut names: Vec<&String> = manager
        .packages()
        .iter()
        .map(|package| package.name())
        .collect();
    names.sort();
    let max_width = 72;
    let max_name_width = 30;
    let mut name_lines = Vec::new();
    let mut current_line = String::with_capacity(80);
    for name in names {
        let display_name = if name.len() > max_name_width {
            format!("{}...", &name[0..20])
        } else {
            name.clone()
        };
        if current_line.is_empty() {
            // If empty add name and continue
            current_line.push_str(&display_name);
        } else {
            // Check if adding will overflow then add
            let new_len = current_line.len() + display_name.len() + 1;
            if new_len > max_width {
                name_lines.push(current_line);
                current_line = String::with_capacity(80);
            } else {
                current_line.push(' ');
            }
            current_line.push_str(&display_name);
        }
    }
    if !current_line.is_empty() {
        name_lines.push(current_line);
    }

    // Build output lines
    let lines = [
        "",
        "Camas' AUR Packager",
        "",
        "Builds, tests and deploys pacman packages",
        "https://github.com/camas/aur-packages/",
        "",
        git_string.as_str(),
        "",
    ];

    // Style and print
    for line in lines.iter() {
        println!("\x1B[1m {:^72} \x1B[0m", line);
    }
    // Lower number 72 as bold text has invisible chars
    for line in name_lines {
        println!(" {:^72} ", line);
    }
    println!();
}

pub fn test_package(
    package_dir: impl AsRef<Path>,
    package: &Package,
    enter_shell: bool,
    skip_makepkg: bool,
    skip_build: bool,
) {
    let package_dir = package_dir.as_ref();

    // Test 1: Shellcheck PKGBUILD
    // Read pkgbuild and stub contents
    let stub = include_bytes!("../static/shellcheck_stub.sh");
    let pkgbuild_path = package_dir.join(package.name()).join("PKGBUILD");
    let pkgbuild = std::fs::read(pkgbuild_path).expect("Couldn't read PKGBUILD");

    // Pipe into shellcheck process
    let mut child = Command::new("shellcheck")
        .arg("-")
        .stdin(Stdio::piped())
        .spawn()
        .expect("Error running shellcheck");
    let child_in = child
        .stdin
        .as_mut()
        .expect("Shellcheck stdin couldn't be captured");
    child_in.write_all(stub).unwrap();
    child_in.write_all(&pkgbuild).unwrap();

    // Check returned successfully
    let status = child.wait().unwrap();
    if !status.success() {
        panic!(format!("Shellcheck of {} PKGBUILD failed", package.name()));
    }

    // Test 2: Install inside docker container
    // Run docker
    if !skip_makepkg {
        if !skip_build {
            build_image(package_dir.parent().unwrap(), false);
        }
        let mut args = vec!["docker", "run", "--tmpfs", "/tmp:exec", "--rm"];
        if enter_shell {
            args.extend(vec!["--env", "AUR_SHELL=True", "-it"]);
        }
        args.extend(vec![DOCKER_TAG, "tester", package.name()]);
        run_command_no_capture("sudo", &args);
    }
}

/// Builds the docker image
///
/// Set `full_build` to true to ignore docker cache
pub fn build_image(base_dir: impl AsRef<Path>, full_build: bool) {
    let base_dir = base_dir.as_ref();

    // Build dockerfile path
    let docker_path = base_dir.join("image").join("Dockerfile");

    // Build args
    let mut args = vec![
        "docker",
        "build",
        "-f",
        docker_path
            .to_str()
            .expect("Couldn't convert path to string"),
        "--tag",
        DOCKER_TAG,
        "--cache-from",
        DOCKER_TAG,
    ];

    // Check for mirrorlist location env var
    let location_arg;
    if let Ok(location) = std::env::var("MIRRORLIST_COUNTRY") {
        args.push("--build-arg");
        location_arg = format!("MIRRORLIST_COUNTRY={}", location);
        args.push(location_arg.as_str());
    }

    if full_build {
        args.push("--no-cache");
    }

    // Push base path for docker context
    args.push(base_dir.to_str().expect("Couldn't write path as string"));

    // Run
    run_command_no_capture("sudo", &args);
}
