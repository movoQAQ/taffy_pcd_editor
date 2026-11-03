//! Standalone probe compiled by region_differential.py; no GUI dependencies.
//! Cargo's automatic integration-test discovery deliberately skips this helper.
#![cfg(not(test))]

#[allow(dead_code)]
#[path = "../src/region.rs"]
mod region;

use std::io::Read;

fn next<T: std::str::FromStr>(tokens: &mut std::str::SplitWhitespace<'_>) -> T
where
    T::Err: std::fmt::Debug,
{
    tokens.next().expect("missing probe input").parse().unwrap()
}

fn main() {
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input).unwrap();
    let mut tokens = input.split_whitespace();
    let cases: usize = next(&mut tokens);
    for _ in 0..cases {
        let pick_count: usize = next(&mut tokens);
        let query_count: usize = next(&mut tokens);
        let expansion: f32 = next(&mut tokens);
        let picks: Vec<[f32; 3]> = (0..pick_count)
            .map(|_| std::array::from_fn(|_| next(&mut tokens)))
            .collect();
        let queries: Vec<[f32; 3]> = (0..query_count)
            .map(|_| std::array::from_fn(|_| next(&mut tokens)))
            .collect();
        let ranges = std::array::from_fn(|_| std::array::from_fn(|_| next(&mut tokens)));
        match region::Region::from_picks(&picks, expansion) {
            Ok(region) => {
                for point in queries {
                    print!(
                        "{}",
                        if region.contains(point, ranges) {
                            '1'
                        } else {
                            '0'
                        }
                    );
                }
                println!();
            }
            Err(error) => println!("ERROR {error}"),
        }
    }
    assert!(tokens.next().is_none(), "unexpected trailing probe input");
}
