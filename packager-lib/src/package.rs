use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;

#[derive(Debug)]
pub struct Package {
    name: String,
    namcap_ignores: Vec<String>,
    config: Config,
}

impl Package {
    /// Initializes a package from a directory
    pub fn from_dir<P>(path: P) -> Package
    where
        P: AsRef<Path>,
    {
        let path = path.as_ref();

        // Read config file
        let config_path = path.join(".settings.yaml");
        let config = if config_path.is_file() {
            let file = File::open(config_path).expect("Error opening config");
            let r = BufReader::new(file);
            serde_yaml::from_reader(r).expect("Error reading package config")
        } else {
            Config {
                upstream: None,
                history: None,
            }
        };
        config.validate().expect("Config isn't valid");

        // Read namcap ignore options if available
        let namcap_ignore_path = path.join(".namcap_ignore");
        let namcap_ignores = if namcap_ignore_path.is_file() {
            let file = File::open(namcap_ignore_path).expect("Error opening namcap ignore file");
            let r = BufReader::new(file);
            // Turns Vec<Result<... into Result<Vec<...
            r.lines()
                .map(|line| line.expect("Couldn't read line"))
                .collect::<Vec<String>>()
        } else {
            vec![]
        };

        // Return package
        Package {
            name: path.file_name().unwrap().to_str().unwrap().to_string(),
            namcap_ignores,
            config,
        }
    }

    pub fn name(&self) -> &String {
        &self.name
    }

    pub fn namcap_ignores(&self) -> &Vec<String> {
        &self.namcap_ignores
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct Config {
    upstream: Option<HashMap<String, String>>,
    history: Option<HashMap<String, String>>,
}

const VALID_UPSTREAM_KEYS: &[&str] = &["pypi", "github"];

impl Config {
    fn validate(&self) -> Result<(), String> {
        // Check upstream keys are valid
        if let Some(dict) = self.upstream.as_ref() {
            for key in dict.keys() {
                if !VALID_UPSTREAM_KEYS.contains(&&**key) {
                    return Err(format!("Invalid upstream type {}", key));
                }
            }
        }
        Ok(())
    }
}
