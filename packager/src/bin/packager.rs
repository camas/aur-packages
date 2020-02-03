use ansi_term::Style;
use clap::{clap_app, crate_authors, crate_version, AppSettings};
use log::*;
use packager::{run_command, PackageManager};
use std::error::Error;
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn Error>> {
    // Parse command line arguments
    let app = clap_app!(("packager") =>
        (version: crate_version!())
        (author: crate_authors!())
        (about: "AUR Package Manager")
        (setting: AppSettings::ArgRequiredElseHelp)
        (@arg verbosity: -v +multiple "Set error verbosity. Repeatable for higher verbosity")
        (@arg directory: -d --package-dir +takes_value "Set package dir to use")
        (@subcommand list =>
            (about: "List packages")
        )
        (@subcommand header =>
            (about: "Show header")
        )
        (@subcommand build =>
            (about: "Build the docker image")
            (@arg full_build: -f --full "Build the image fully")
        )
    );
    let matches = app.get_matches();

    // Init logging
    let verbosity = if cfg!(debug_assertions) {
        4
    } else {
        matches.occurrences_of("verbosity") as usize
    };
    stderrlog::new()
        .module(module_path!())
        .verbosity(verbosity)
        .timestamp(stderrlog::Timestamp::Microsecond)
        .init()?;
    trace!("Logger initialized");

    // Start package manager
    let dir = if let Some(d) = matches.value_of("directory") {
        PathBuf::from(d)
    } else {
        PathBuf::from("packages")
    };
    let manager = PackageManager::from_dir(&dir)?;

    // Handle sub command
    trace!("Handling command, if any");
    if matches.subcommand_matches("list").is_some() {
        list_packages(manager)?;
    } else if matches.subcommand_matches("header").is_some() {
        print_header(manager)?;
    } else if let Some(matches) = matches.subcommand_matches("build") {
        let full_build = matches.is_present("full_build");
        manager.build_image(full_build)?;
    } else {
        // If none print header then help message
        print_header(manager)?;
        println!(
            " {:^72} ",
            "To see the help for this program pass -h or --help"
        );
        println!();
    }

    trace!("Exiting");
    Ok(())
}

/// Display a list of all packages
fn list_packages(manager: PackageManager) -> Result<(), Box<dyn Error>> {
    trace!("Listing packages");
    let packages = manager.get_packages();
    println!("{} packages:", packages.len());
    for package in packages {
        println!("{:<32}    VERSIONTODO-RELEASETODO", package.get_name());
    }
    Ok(())
}

/// Print a formatted header
fn print_header(manager: PackageManager) -> Result<(), Box<dyn Error>> {
    trace!("Printing header");

    // Get git info
    let git_branch_output = run_command("git", &["rev-parse", "--abbrev-ref", "HEAD"])?;
    let git_branch = git_branch_output.lines().next().ok_or("No output")?;
    let git_hash_output = run_command("git", &["rev-list", "-n", "1", "HEAD"])?;
    let git_hash = git_hash_output.lines().next().ok_or("No output")?;
    let git_commits_output = run_command("git", &["rev-list", "--count", "HEAD"])?;
    let git_commits = git_commits_output.lines().next().ok_or("No output")?;
    let git_string = format!(
        "{} | {} | {} commits",
        git_branch,
        &git_hash[..8],
        git_commits
    );

    // Get and format package names
    let mut names = manager.get_package_names();
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
    let bold = Style::new().bold();
    for line in lines.iter() {
        println!(" {:^80} ", format!("{}", bold.paint(*line)));
    }
    // Lower number 72 as bold text has invisible chars
    for line in name_lines {
        println!(" {:^72} ", line);
    }
    println!();

    Ok(())
}
