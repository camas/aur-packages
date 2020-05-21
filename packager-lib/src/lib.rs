use std::process::Command;

mod manager;
mod package;

pub use crate::manager::PackageManager;
pub use crate::package::Package;

/// Runs a command, capturing all output and returning stdout
pub fn run_command(command: &str, args: &[&str]) -> String {
    let output = Command::new(command)
        .args(args)
        .output()
        .expect("Error running command");
    if !output.status.success() {
        let error_code = output.status.code().expect("No error code returned");
        let error_string = format!(
            "Command {} {:?} failed with error code {}",
            command, args, error_code
        );
        panic!(error_string);
    }
    String::from_utf8(output.stdout).unwrap()
}

/// Runs a command without capturing any output
pub fn run_command_no_capture(command: &str, args: &[&str]) {
    let status = Command::new(command)
        .args(args)
        .spawn()
        .expect("Error running command")
        .wait()
        .unwrap();
    if !status.success() {
        let error_code = status.code().expect("No error code returned");
        let error_string = format!(
            "Command {} {:?} failed with error code {}",
            command, args, error_code
        );
        panic!(error_string);
    }
}

pub fn run_premade_command(command: &mut Command) {
    let status = command.spawn().unwrap().wait().unwrap();
    if !status.success() {
        let error_code = status.code().expect("No error code returned");
        let error_string = format!(
            "Command {:?} failed with error code {}",
            command, error_code
        );
        panic!(error_string);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env;

    #[test]
    fn test_run_command() {
        let result = run_command("echo", &["howdy"]);
        assert_eq!(result, "howdy\n");

        let wd = env::current_dir().unwrap();
        let result = run_command("pwd", &[]);
        assert_eq!(result, format!("{}\n", wd.to_str().unwrap()));
    }
}
