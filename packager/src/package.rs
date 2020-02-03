use log::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::error::Error;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;

#[derive(Debug)]
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

        // Read config file
        let mut config_path = path.clone();
        config_path.push(".settings.yaml");
        let config = if config_path.is_file() {
            let file = File::open(config_path)?;
            let r = BufReader::new(file);
            serde_yaml::from_reader(r)?
        } else {
            Config {
                upstream: None,
                history: None,
            }
        };
        config.validate()?;
        trace!("Loaded config: {:?}", config);

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
        trace!("Loaded namcap ignores: {:?}", namcap_ignores);

        // Return package
        Ok(Package {
            name: name.to_str().unwrap().to_string(),
            namcap_ignores,
        })
    }

    pub fn get_name(&self) -> &String {
        &self.name
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct Config {
    upstream: Option<HashMap<String, String>>,
    history: Option<HashMap<String, String>>,
}

const VALID_UPSTREAM_KEYS: &[&str] = &["pypi", "github"];

impl Config {
    fn validate(&self) -> Result<(), Box<dyn Error>> {
        // Check upstream keys are valid
        if let Some(dict) = self.upstream.as_ref() {
            for key in dict.keys() {
                if !VALID_UPSTREAM_KEYS.contains(&&**key) {
                    return Err(format!("Invalid upstream type {}", key).into());
                }
            }
        }
        Ok(())
    }
}
