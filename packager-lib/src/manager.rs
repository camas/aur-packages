use crate::Package;
use std::path::{Path, PathBuf};

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
    /// * `path` - The base path to work from that contains each package as a directory
    pub fn from_dir(path: impl AsRef<Path>) -> PackageManager {
        let path = path.as_ref();
        let mut packages = Vec::new();
        for entry in path.read_dir().unwrap() {
            let entry = entry.unwrap();
            // Skip files
            if !entry.file_type().unwrap().is_dir() {
                continue;
            }
            let package = Package::from_dir(&entry.path());
            packages.push(package);
        }
        PackageManager {
            packages,
            base_path: path.to_path_buf(),
        }
    }

    pub fn packages(&self) -> &Vec<Package> {
        &self.packages
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_working() {
        PackageManager::from_dir("packages");
    }
}
