use clap::{clap_app, crate_authors, crate_version};
use log::*;
use packager::aur::calc_aur_deps;
use packager::{run_command_no_capture, run_premade_command};
use std::env;
use std::error::Error;
use std::fs;
use std::process::Command;

fn main() -> Result<(), Box<dyn Error>> {
    // Parse command line arguments
    let matches = clap_app!(("package tester") =>
        (version: crate_version!())
        (author: crate_authors!())
        (about: "Pacman Package Tester")
        (@arg package: +required "The package to test")
    )
    .get_matches();

    // Init logging
    stderrlog::new()
        .module(module_path!())
        .verbosity(4)
        .timestamp(stderrlog::Timestamp::Microsecond)
        .init()?;
    trace!("Logger initialized");

    let package_name = matches.value_of("package").ok_or("No package specified")?;

    // Install package
    install_package(&package_name)?;

    // Run namcap

    Ok(())
}

fn install_package(package_name: &str) -> Result<(), Box<dyn Error>> {
    // Calculate dependencies
    let deps = calc_aur_deps(&package_name)?;
    info!("Found package and dependencies: {:?}", deps);

    // Install package and dependencies
    let client = reqwest::blocking::Client::builder()
        .user_agent("Aur package tester (https://github.com/camas/)")
        .build()?;
    for (i, dep) in deps.iter().enumerate() {
        trace!("Installing package {}", dep);

        // Open tmp file
        let tmp_package_path = env::temp_dir().join("aur-packages");
        trace!("Creating dir {}", tmp_package_path.display());
        fs::create_dir(&tmp_package_path)?;
        let tmp_path = tmp_package_path.join(dep);
        trace!("Creating dir {}", tmp_path.display());
        fs::create_dir(&tmp_path)?;
        let file_path = tmp_path.join("package.tar.gz");
        trace!("Opening temp file {:?}", file_path);
        let mut file = fs::File::create(&file_path)?;

        // Download pkgbuild from aur
        let url = format!(
            "https://aur.archlinux.org/cgit/aur.git/snapshot/{}.tar.gz",
            dep
        );
        info!("Downloading {}", url);
        let mut resp = client.get(&url).send()?;
        std::io::copy(&mut resp, &mut file)?;
        trace!("Downloaded");

        // Extract and install
        run_command_no_capture(
            "tar",
            &[
                "--extract",
                &format!("--file={}", file_path.display()),
                &format!("--directory={}", tmp_path.display()),
            ],
        )?;
        let pkgbuild_path = tmp_path.join(dep);
        let mut makepkg_command = Command::new("makepkg");
        makepkg_command.current_dir(pkgbuild_path).args(&[
            "--syncdeps",
            "--install",
            "--noconfirm",
        ]);
        if i != deps.len() - 1 {
            makepkg_command.arg("--asdeps");
        }
        run_premade_command(&mut makepkg_command)?;
        info!("Installed dependency {}", dep);
    }

    Ok(())
}
