use crate::{run_command_no_capture, Package};
use log::*;
use std::env;
use std::error::Error;
use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

const DOCKER_TAG: &str = "camas/aur-packages";

#[derive(Debug)]
pub struct PackageManager {
    packages: Vec<Package>,
    base_path: PathBuf,
}

impl PackageManager {
    /// Initializes the package manager
    ///
    /// ## Arguments
    ///
    /// * `path` - The base path to work from that includes the 'packages' and 'image' directories
    pub fn from_dir(path: &PathBuf) -> Result<PackageManager, Box<dyn Error>> {
        debug!("Initializing package manager using '{}'", path.display());
        let mut packages = Vec::new();
        let mut pkg_path = path.clone();
        pkg_path.push("packages");
        for entry_res in pkg_path.read_dir()? {
            let entry = entry_res?;
            if !entry.file_type()?.is_dir() {
                warn!(
                    "File '{:?}' in package directory. Ignoring",
                    entry.file_name()
                );
            }
            let package = Package::from_dir(&entry.path())?;
            packages.push(package);
        }
        debug!("Loaded {} packages", packages.len());
        Ok(PackageManager {
            packages,
            base_path: path.clone(),
        })
    }

    pub fn get_packages(&self) -> &Vec<Package> {
        &self.packages
    }

    pub fn get_package_names(&self) -> Vec<&String> {
        self.packages.iter().map(|x| x.get_name()).collect()
    }

    pub fn get_package_by_name(&self, name: &str) -> Result<&Package, Box<dyn Error>> {
        self.packages
            .iter()
            .find(|x| x.get_name() == name)
            .ok_or_else(|| format!("No package exists with the name {}", name).into())
    }

    pub fn build_image(&self, full_build: bool) -> Result<(), Box<dyn Error>> {
        trace!("Building image with full_build: {}", full_build);

        // Build dockerfile path
        let mut docker_path = self.base_path.clone();
        docker_path.push("image");
        docker_path.push("Dockerfile");

        // Build args
        let mut args = vec![
            "docker",
            "build",
            "-f",
            docker_path
                .to_str()
                .ok_or("Couldn't convert path to string")?,
            "--tag",
            DOCKER_TAG,
            "--cache-from",
            DOCKER_TAG,
        ];

        // Check for mirrorlist location env var
        let location_arg;
        if let Ok(location) = env::var("MIRRORLIST_COUNTRY") {
            trace!("MIRRORLIST_COUNTRY set. Using location {}", location);
            args.push("--build-arg");
            location_arg = format!("MIRRORLIST_COUNTRY={}", location);
            args.push(location_arg.as_str());
        }

        if full_build {
            args.push("--no-cache");
        }

        // Push base path for docker context
        args.push(
            self.base_path
                .to_str()
                .ok_or("Couldn't write path as string")?,
        );

        // Run
        run_command_no_capture("sudo", &args)?;

        Ok(())
    }

    pub fn test_package(&self, package: &Package, enter_shell: bool) -> Result<(), Box<dyn Error>> {
        trace!("Testing package {}", package.get_name());

        // Test 1: Shellcheck PKGBUILD
        // Read pkgbuild and stub contents
        let stub = include_bytes!("../static/shellcheck_stub.sh");
        let pkgbuild = self.read_pkgbuild(package)?;

        // Pipe into shellcheck process
        trace!("Running shellcheck");
        let mut child = Command::new("shellcheck")
            .arg("-")
            .stdin(Stdio::piped())
            .spawn()?;
        let child_in = child
            .stdin
            .as_mut()
            .ok_or("Shellcheck stdin couldn't be captured")?;
        child_in.write_all(stub)?;
        child_in.write_all(&pkgbuild)?;

        // Check returned successfully
        let status = child.wait()?;
        if !status.success() {
            return Err(format!("Shellcheck of {} PKGBUILD failed", package.get_name()).into());
        }

        // Test 2: Install inside docker container
        // Run docker
        trace!("Running docker");
        self.build_image(false)?;
        let mut args = vec!["docker", "run", "--tmpfs", "/tmp:exec", "--rm"];
        if enter_shell {
            args.extend(vec!["--env", "AUR_SHELL=True", "-it"]);
        }
        args.extend(vec![DOCKER_TAG, "package_tester", package.get_name()]);
        run_command_no_capture("sudo", &args)?;

        Ok(())
    }

    fn read_pkgbuild(&self, package: &Package) -> Result<Vec<u8>, std::io::Error> {
        debug!("Reading PKGBUILD for {}", package.get_name());

        let mut path = self.base_path.clone();
        path.push("packages");
        path.push(package.get_name());
        path.push("PKGBUILD");

        fs::read(path)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_working() {
        let path = PathBuf::from("../");
        PackageManager::from_dir(&path).unwrap();
    }
}
