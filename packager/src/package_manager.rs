use crate::Package;
use log::*;
use std::error::Error;
use std::path::PathBuf;

#[derive(Debug)]
pub struct PackageManager {
    packages: Vec<Package>,
}

impl PackageManager {
    /// Initializes a package manager from a directory of packages
    pub fn from_dir(path: &PathBuf) -> Result<PackageManager, Box<dyn Error>> {
        debug!("Initializing package manager using '{}'", path.display());
        let mut packages = Vec::new();
        for entry_res in path.read_dir()? {
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
        Ok(PackageManager { packages })
    }

    pub fn get_packages(&self) -> &Vec<Package> {
        &self.packages
    }

    pub fn get_package_names(&self) -> Vec<&String> {
        self.packages.iter().map(|x| x.get_name()).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_working() {
        let path = PathBuf::from("../packages");
        PackageManager::from_dir(&path).unwrap();
    }
}
