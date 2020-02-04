use log::*;
use std::error::Error;
use std::process::Command;

mod package;
mod package_manager;

pub use self::package::Package;
pub use self::package_manager::PackageManager;

/// Runs a command, capturing all output and returning stdout
pub fn run_command(command: &str, args: &[&str]) -> Result<String, Box<dyn Error>> {
    debug!("Running command {} with args {:?}", command, args);
    let output = Command::new(command).args(args).output()?;
    if !output.status.success() {
        let error_code = output.status.code().ok_or("No error code returned")?;
        let error_string = format!(
            "Command {} {:?} failed with error code {}",
            command, args, error_code
        );
        return Err(error_string.into());
    }
    Ok(String::from_utf8(output.stdout)?)
}

/// Runs a command without capturing any output
pub fn run_command_no_capture(command: &str, args: &[&str]) -> Result<(), Box<dyn Error>> {
    debug!("Running command {} with args {:?}", command, args);
    let status = Command::new(command).args(args).spawn()?.wait()?;
    if !status.success() {
        let error_code = status.code().ok_or("No error code returned")?;
        let error_string = format!(
            "Command {} {:?} failed with error code {}",
            command, args, error_code
        );
        return Err(error_string.into());
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env;

    #[test]
    fn test_run_command() {
        let result = run_command("echo", &["howdy"]).unwrap();
        assert_eq!(result, "howdy\n");

        let wd = env::current_dir().unwrap();
        let result = run_command("pwd", &[]).unwrap();
        assert_eq!(result, format!("{}\n", wd.to_str().unwrap()));
    }
}
