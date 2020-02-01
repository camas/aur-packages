use clap::{clap_app, crate_authors, crate_version};
use log::*;
use packager::PackageManager;
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Parse command line arguments
    let matches = clap_app!(("packager") =>
        (version: crate_version!())
        (author: crate_authors!())
        (about: "AUR Package Manager")
        (@arg verbosity: -v +multiple "Set error verbosity. Repeatable for higher verbosity")
    )
    .get_matches();

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
    let dir = PathBuf::from("./packages");
    let manager = PackageManager::from_dir(&dir)?;

    Ok(())
}
