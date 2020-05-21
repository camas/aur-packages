use clap::{clap_app, crate_authors, crate_version};
use packager_lib::{run_command, run_command_no_capture, Package, PackageManager};
use std::env;
use std::path::Path;
use std::process::Command;

fn main() {
    // Parse command line arguments
    let matches = clap_app!(("package tester") =>
        (version: crate_version!())
        (author: crate_authors!())
        (about: "Pacman Package Tester")
        (@arg package: +required "The package to test")
    )
    .get_matches();

    let package_name = matches.value_of("package").expect("No package specified");

    let manager = PackageManager::from_dir("/packages");
    let package = manager
        .packages()
        .iter()
        .find(|package| package.name() == package_name)
        .expect("No package with the specified name");

    // Install package
    install_package(&package);

    // Install testing packages
    run_command_no_capture(
        "sudo",
        &[
            "pacman",
            "-Su",
            "--noconfirm",
            "--cachedir",
            "/pacman-cache",
            "namcap",
        ],
    );

    // Run namcap
    let dir = Path::new("/packages").join(package_name);
    let pkgbuild_path = dir.join("PKGBUILD");
    let pkg_path = dir
        .read_dir()
        .unwrap()
        .map(|entry| entry.unwrap())
        .find(|entry| entry.file_name().to_str().unwrap().ends_with(".pkg.tar"))
        .unwrap()
        .path();
    let output = run_command(
        "namcap",
        &[pkgbuild_path.to_str().unwrap(), pkg_path.to_str().unwrap()],
    );
    let difference: Vec<&str> = output
        .lines()
        .filter(|line| !package.namcap_ignores().contains(&line.trim().to_string()))
        .collect();
    if !difference.is_empty() {
        difference.iter().for_each(|line| println!("{}", line));
        panic!("Namcap found issues");
    }

    println!();
    println!("\x1B[1mTesting successful\x1B[0m");
}

fn install_package(package: &Package) {
    // Calculate dependencies by generating .SRCINFO then parsing it
    let dir = Path::new("/packages").join(package.name());
    let mut command = Command::new("makepkg");
    let output = command
        .current_dir(&dir)
        .arg("--printsrcinfo")
        .output()
        .unwrap();
    if !output.status.success() {
        panic!();
    }
    let srcinfo = String::from_utf8(output.stdout).unwrap();
    let deps: Vec<&str> = srcinfo
        .lines()
        .map(|line| line.trim())
        .filter(|line| line.starts_with("makedepends ") || line.starts_with("depends "))
        .map(|line| line.splitn(2, '=').nth(1).unwrap().trim())
        .collect();

    // Install dependencies using yay
    let mut args = vec!["-S", "--noconfirm", "--needed", "--asdeps"];
    args.extend(deps);
    run_command_no_capture("yay", &args);

    // Build and install using makepkg
    let mut command = Command::new("makepkg");
    let status = command
        .current_dir(&dir)
        .arg("-i")
        .arg("--noconfirm")
        .spawn()
        .unwrap()
        .wait()
        .unwrap();
    if !status.success() {
        panic!();
    }
    println!("\x1B[1mInstalled successfully\x1B[0m");
}
