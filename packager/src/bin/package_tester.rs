use clap::{clap_app, crate_authors, crate_version};
use log::*;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Parse command line arguments
    let _ = clap_app!(("package tester") =>
        (version: crate_version!())
        (author: crate_authors!())
        (about: "Pacman Package Tester")
    )
    .get_matches();

    // Init logging
    stderrlog::new()
        .module(module_path!())
        .verbosity(4)
        .timestamp(stderrlog::Timestamp::Microsecond)
        .init()?;
    trace!("Logger initialized");

    Ok(())
}
