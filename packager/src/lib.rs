use log::*;
use std::error::Error;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;

pub struct Package {
    name: String,
    namcap_ignores: Vec<String>,
}

impl Package {
    /// Initializes a package from a directory
    pub fn from_dir(path: &PathBuf) -> Result<Package, Box<dyn Error>> {
        debug!("Reading package info from {}", path.display());
        // Get name from dir
        let name = path.file_name().ok_or("Couldn't read path name")?;
        // Read namcap ignore options if available
        let mut namcap_ignore_path = path.clone();
        namcap_ignore_path.push(".namcap_ignore");
        let namcap_ignores = if namcap_ignore_path.is_file() {
            let file = File::open(namcap_ignore_path)?;
            let r = BufReader::new(file);
            // Turns Vec<Result<... into Result<Vec<...
            r.lines().collect::<Result<Vec<String>, _>>()?
        } else {
            vec![]
        };
        trace!("{} namcap ignores", namcap_ignores.len());
        // Return package
        Ok(Package {
            name: name.to_str().unwrap().to_string(),
            namcap_ignores,
        })
    }
}

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
        Ok(PackageManager { packages })
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
