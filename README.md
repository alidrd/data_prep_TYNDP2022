**TYNDP 2022 Python Analysis Repository**

This repository contains Python code for analyzing the TYNDP 2022
dataset focusing on demand, NTC (Net Transfer Capacity), and reserve
data.

**Installation**

1.  **Clone this repository:**

> Bash
>
> git clone https://github.com/alidrd/data_prep_TYNDP2022.git
>
> content_copy

2.  **Install dependencies:**

> Bash
>
> pip install -r requirements.txt
>
> content_copy

**Dataset**

- Download the TYNDP 2022 dataset from the provided SharePoint link
  (https://zhaw-my.sharepoint.com/:f:/g/personal/daru_zhaw_ch/Eo5SHpilb85Ij-NT38tPJhoBIjamu1zvJ_CNN7v3sxnNzg?e=s9Lbjk{.underline}).

- Extract the downloaded files to a folder on your disk.

- **Important:** Modify the climate_data_dir variable in all code
  files (particularly data_prep_for_model.py) to point to the
  directory containing the extracted dataset files.

**Code Files**

This repository includes the following Python code files:

- data_prep_for_model_demand_data_reader.py: Processes demand data
  from the TYNDP 2022 dataset.

- data_prep_for_model_ntc_data_reader.py: Processes NTC data from the
  TYNDP 2022 dataset.

- data_prep_for_model_res_data_reader.py: Processes reserve data from
  the TYNDP 2022 dataset.

- data_prep_for_model.py: Combines and prepares data from the previous
  three files for further analysis. Note that before this script, electrolysis_demand_read.py, tyndp22_flows.py, and cap_gen_read.py need to be executed.
