import pandas as pd
import subprocess

base_profile_path = 'results_archive/01-02-2-rene/profile.csv'
target_configuration_path = 'configuration.yml'
target_bandwidth_limit_path = '../dataset/rene/bandwidthLimit.yml'

profile = pd.read_csv(base_profile_path)

for bandwidth in profile['bandwidth']:
    subprocess.run(f"yq -yi '.default.adaptive_test_display = {bandwidth}' {target_configuration_path}", shell = True)
    subprocess.run(f"yq -yi '.bandwidth_limit = {[bandwidth]*4}' {target_bandwidth_limit_path}", shell = True)
    subprocess.run("python entrance.py", shell = True)