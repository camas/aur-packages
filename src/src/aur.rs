use log::*;
use serde::{self, Deserialize, Serialize};
use std::collections::HashSet;
use std::error::Error;

/// Calculates the order in which aur dependencies will need to be installed
///
/// ## Arguments
///
/// * `package` - The package to start from
pub fn calc_aur_deps(package: &str) -> Result<Vec<String>, Box<dyn Error>> {
    trace!("Calculating dependency install order for {}", package);

    // Init http client
    let base_url = "https://aur.archlinux.org/rpc/?v=5&type=info&arg[]=";
    let client = reqwest::blocking::Client::builder()
        .user_agent("Aur package tester (https://github.com/camas/)")
        .build()?;

    // Loop until all dependencies resolved
    let mut done = HashSet::new();
    let mut infos = Vec::new();
    let mut to_do = vec![package.to_string()];
    while !to_do.is_empty() {
        // Pop packages until url too long
        let mut cur_len = base_url.len();
        let mut to_use = vec![];
        loop {
            if to_do
                .last()
                .map_or(false, |x| cur_len + x.len() + 7 <= 4443)
            {
                let p = to_do.pop().ok_or("Couldn't pop")?;
                cur_len += p.len() + 7;
                to_use.push(p.clone());
                done.insert(p);
            } else {
                break;
            }
        }

        // Make request
        let url = format!("{}{}", base_url, to_use.join("&arg[]="));
        debug!("Making GET request to {}", url);
        let resp = client.get(&url).send()?;

        // Handle results
        trace!("Handling results");
        let resp_data: InfoResponse = resp.json()?;
        resp_data.validate()?;
        for info in resp_data.results {
            for dep in info.get_depends() {
                if dep.contains('=') {
                    warn!("Unusual char found in dependency {}", dep);
                }
                if !dep.contains('=') && !done.contains(dep.as_str()) {
                    to_do.push(dep.clone());
                }
            }

            infos.push(info);
        }
    }

    // If empty it isn't an AUR package
    if infos.is_empty() {
        return Ok(vec![package.to_string()]);
    }

    // Calculate order
    let mut install_order = Vec::new();
    while !infos.is_empty() {
        let next_index = infos
            .iter()
            .position(|info| {
                // Check all dependencies
                for dep in info.get_depends() {
                    if infos.iter().any(|x| x.name == *dep) {
                        return false;
                    }
                }
                true
            })
            .ok_or("Circular dependencies?")?;
        // Remove from queue and add to end of install list
        let next = infos.swap_remove(next_index);
        install_order.push(next.name);
    }

    assert_eq!(install_order.last().unwrap(), package);

    // Return
    Ok(install_order)
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct InfoResponse {
    pub version: i64,
    #[serde(rename = "type")]
    pub type_field: String,
    pub resultcount: i64,
    pub results: Vec<PackageInfo>,
}

impl InfoResponse {
    fn validate(&self) -> Result<(), Box<dyn Error>> {
        if self.version != 5 {
            return Err("Wrong version in api response".into());
        }
        if self.type_field != "multiinfo" {
            return Err("Wrong type in api response".into());
        }
        Ok(())
    }
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PackageInfo {
    // #[serde(rename = "ID")]
    // pub id: i64,
    #[serde(rename = "Name")]
    pub name: String,
    // #[serde(rename = "PackageBaseID")]
    // pub package_base_id: i64,
    // #[serde(rename = "PackageBase")]
    // pub package_base: String,
    // #[serde(rename = "Version")]
    // pub version: String,
    // #[serde(rename = "Description")]
    // pub description: String,
    // #[serde(rename = "URL")]
    // pub url: String,
    // #[serde(rename = "NumVotes")]
    // pub num_votes: i64,
    // #[serde(rename = "Popularity")]
    // pub popularity: i64,
    // #[serde(rename = "OutOfDate")]
    // pub out_of_date: ::serde_json::Value,
    // #[serde(rename = "Maintainer")]
    // pub maintainer: String,
    // #[serde(rename = "FirstSubmitted")]
    // pub first_submitted: i64,
    // #[serde(rename = "LastModified")]
    // pub last_modified: i64,
    // #[serde(rename = "URLPath")]
    // pub urlpath: String,
    #[serde(rename = "Depends")]
    pub depends: Option<Vec<String>>,
    #[serde(rename = "MakeDepends")]
    pub make_depends: Option<Vec<String>>,
    // #[serde(rename = "Conflicts")]
    // pub conflicts: Vec<String>,
    // #[serde(rename = "Provides")]
    // pub provides: Vec<String>,
    // #[serde(rename = "License")]
    // pub license: Vec<String>,
    // #[serde(rename = "Keywords")]
    // pub keywords: Vec<::serde_json::Value>,
}

impl PackageInfo {
    fn get_depends(&self) -> Vec<&String> {
        let mut deps = vec![];
        if let Some(d) = self.depends.as_ref() {
            deps.extend(d.iter());
        }
        if let Some(d) = self.make_depends.as_ref() {
            deps.extend(d.iter());
        }
        deps
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calc_deps() {
        calc_aur_deps("mopidy-mopify").unwrap();
    }
}
