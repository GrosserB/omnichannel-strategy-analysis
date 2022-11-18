# Evaluation of Omnichannel Strategy at Berlin-based E-Commerce Company: Do Offline Showrooms Increase Online Sales?

## Summary
This project uses confidential online sales data from a Berlin-based e-commerce firm to estimate the causal effect of offline showrooms on online sales. We employ synthetic control methods, nearest neighbor matching, and difference-in-differences methods to estimate the causal parameters. The results of our analyses suggest that a showroom increases online sales in the area surrounding the showroom by 7-20%. The numbers are statistically and economically significant; the more credible estimates are at the lower end of the range. In combination with the costs of operating these stores, the "Showroom ROI" can be obtained and compared to that of other marketing channels. Therefore, this project provides important inputs that support strategic decision-making on the optimal marketing mix.


"
![Aggregated Difference-in-Differences Plot](./output/image_name.png)
"

*These results show the average difference-in-difference estimators at the lenght of exposure in quarters*


Authors:
Benjamin Grosse-Rueschkamp, Linkedin: https://www.linkedin.com/in/benjamingrosserueschkamp, Github: https://github.com/GrosserB
Michael Dietrich, Linkedin:, Github:

Note: The Core data used for this project is confidential, hence any information shown here that could identify the firm (e.g. showroom location or absolute numbers) are fictional. This project is work-in-progress.


## Table of Contents


https://stackoverflow.com/questions/11948245/markdown-to-create-pages-and-table-of-contents

https://community.atlassian.com/t5/Bitbucket-questions/How-to-write-a-table-of-contents-in-a-Readme-md/qaq-p/673363

https://github.com/ekalinin/github-markdown-toc



## Description
### Objective

Fundamentally,
One of the central marketing challenges is to decide on the spending on different channels to optimize overall sales but knowing the ROI of different channels is challenging.

Product and brand information offline, but filfillment online (with some exceptions, see outlets)

uncertainty of buying online

What is the question? Why does it matter?
-> in essence, a marketing-attribution problem, central to marketing/sales strategy,

Does the opening of showrooms increase online sales?

### Analyses & Results

#### Data and Introduction

We start by cleaning and preprocessing of the data (LINK). We aggregate online sales data on the year-quarter level. We also aggregate sales on postal code area level, and geocode the location of the showrooms and of each postal code. We then computed the distance between each showroom-postal code pair. We define areas as "treated" if their location is <50km from a showroom that opened during our sample period (some showrooms opened before). We additionally augment the dataset with the average population density and credit score of the postal code area (LINK TO DATA DESCRIPTION).

The challenge - as usual with causal inference - is to ensure that we don't misinterpret mere correlations as causal, but instead recover as accurate as possible the "true" parameters. A particular concern in this setting are potentially hidden factors that impact sales and that are also correlated to treatment ("omitted variable bias"). For example, showrooms are opened in urban areas. At the same time, consumers in urban areas exhibit different online shopping behaviors even in the absence of treatment, e.g. the covid lockdowns had a differential impact on urban and rural consumer behavior. Therefore, comparisons of online sales in areas with showrooms vs. those without, or simple before-after comparisons are likely to be biased and would lead to misleading conclusions.

PLOT "Pandemic_Growth_by_PopulationDensity"
*brief description of plot*

To tackle these challenges and obtain robust estimates, we employ three state-of-the-art methodologies from the causal inference toolkit: (1) event-study difference-in-differences with k-nearest neigbors to select the control group, (2) synthetic control methods, and (3) heterogenous-robust two-way fixed-effects difference-in-difference estimation methods

#### Event-study Difference-in-Differences with K-Nearest Neighbors

First, we use nearest neighbor matching to build a control group

1) Plotting online sales in the treated areas vs. those of a matched control group:

PLOT

Interpretation: before the opening of the showroom, online sales grow at similar rates. After the showroom opens, the times series diverge and the areas around the showroom increasing their online order volume at a faster rate.


2) Running an event study-type difference-in-differences analysis

The following table shows the results of the following regression, where [description of the parameters]

LATEX: regression equation

SCREENSHOT TABLE





#### Synthetic Control Method


3) Synthetic Control Method

PLOT


#### Two-way Fixed-effects Difference-in-Difference



4) Aggregated Fixed Effects Difference-in-Differences Analysis

LATEX: regression equation

PLOT

SCREENSHOT TABLE

Interpretation: as with the simple difference-in-differences analysis


#### Discussion



Summary of results: We regard the results of the analyses as robust evidence of a significant effect of offline showrooms on online sales.




all methods employed here are quasi-experimental and attempt to guard against omitted variable bias. However, valid conclusions require assumptions. In particular





which is most credible

what are threats/potential limitations




As with all approaches to causal inference on non-experimental data, valid conclusions require strong assumptions. This method assumes that the outcome of the treated unit can be explained in terms of a set of control units that were themselves not affected by the intervention. Furthermore, the relationship between the treated and control units is assumed to remain stable during the post-intervention period. Including only control units in your dataset that meet these assumptions is critical to the reliability of causal estimates.


Screenshots/Pictures
Cursory discussion of results: what do the numbers say, what is our interpretation/how do we combine these results from the different methods, how much do we trust the results/what are potential limitations

### So-What

Input here the computer on estimated revenue


The results on the impact of opening additional showrooms is to be set in relation to the costs to compute the marketing ROI. This needs to be compared to the ROI of alternative marketing strategies, in particular, performance-marketing.


## Overview



### File Structure

### Authors, Acknowledgements

Thanking Valentin
Early contributions by acknowledge by Jian and Jean
Thanking the anonymous Berlin-based e-commerce company



## Detailed Project Description

### Overview

All parts of the analysis are documented in the jupyter notebook `Main_Project_Notebook.ipynb` together with step-by-step explanations of methods. We provided an example dataset that serves as a basis to explain our approach. It can also be used by anyone to replicate our results.

Disclaimer: Due to confidentiality reasons, the data and final results shown in this project have been significantly altered. Nevertheless, the findings and methods presented here are, generally speaking, a proof of concept, but have been applied successfully to the original dataset.

In this package we made extensive use of [OscarEngelbrektson / SyntheticControlMethods](https://github.com/OscarEngelbrektson/SyntheticControlMethods). We are very grateful for all the work that has been put into those packages.


### Objectives

As mentioned in the Introduction, the goal of our analysis was to determine and measure the effect of physical stores on the online sales of an online retailer.

At the heart of our analysis lay the question: 'Do physical stores have a positive impact on online sales?' 'Do physical stores increase the online sales in a given city?'


### Methods Used

To answer this question, it is imperative to not only rely on classical methods of statistical inference, that usually only achieve insights into correlation of certain phenomena. But to convincingly portray the causal relationship of the matter at hand: between the opening of a store and a possible increase of online sales.

For this purpose, we ...

`More Detailed Explanation of Causal Inference`

- Synthetic Control Method
- Alternatve Control Group
- ...


### Installation

The package can be installed by downloading the contents of this repository/package, navigate to the folder on your command line and typing the following command:

`pip install .`

This will install the contents of this package to your current python environment. Then you should be able to use the notebooks in this package without any trouble. This also enables you to use our method for your own projects.


### Data Processing / Preparation / Loading / Saving

For the purpose of publication, all parts of the analysis start with a dataset, that has already been extensively preprocessed.

For anyone who wants to use our approach for a similar analysis, we give a detailed description of the preprocessed dataset, it's variables and data types. See also the dataset we provided.

`Description of all columns and their data types and contents`


### Further Insights Into Data Preprocessing

As mentioned above, the original data has been significantly altered to comply with a confidentiality agreement. But, the original preprocessing steps for this project have been preserved in `Data_Preprocessing_Notebook.ipynb` and can be accessed in the `notebooks` folder.

Also, the original project used Google's Cloud Storage and BigQuery to store and load the large amounts of data (millions of observations) that would have otherwise exceeded the memory capacity of our machines. Through several preprocessing steps that combined those observations, the data was reduced to merely 400.000 rows, that fit into a single csv file of less than 100MB. A small tutorial on the usage of Google's Cloud Storage and BigQuery for this project is also available in the `Documentation.md` file.



------------------------------------
# Bootcamp Legacy Contents

# Startup the project

The initial setup.

Create virtualenv and install the project:
```bash
sudo apt-get install virtualenv python-pip python-dev
deactivate; virtualenv ~/venv ; source ~/venv/bin/activate ;\
    pip install pip -U; pip install -r requirements.txt
```

Unittest test:
```bash
make clean install test
```

Check for MultiChannelStrategy in gitlab.com/{group}.
If your project is not set please add it:

- Create a new project on `gitlab.com/{group}/MultiChannelStrategy`
- Then populate it:

```bash
##   e.g. if group is "{group}" and project_name is "MultiChannelStrategy"
git remote add origin git@github.com:{group}/MultiChannelStrategy.git
git push -u origin master
git push -u origin --tags
```

Functionnal test with a script:

```bash
cd
mkdir tmp
cd tmp
MultiChannelStrategy-run
```

# Installation

Go to `https://github.com/{group}/MultiChannelStrategy` to see the project, manage issues,
setup you ssh public key, ...

Create a python3 virtualenv and activate it:

```bash
sudo apt-get install virtualenv python-pip python-dev
deactivate; virtualenv -ppython3 ~/venv ; source ~/venv/bin/activate
```

Clone the project and install it:

```bash
git clone git@github.com:{group}/MultiChannelStrategy.git
cd MultiChannelStrategy
pip install -r requirements.txt
make clean install test                # install and test
```
Functionnal test with a script:

```bash
cd
mkdir tmp
cd tmp
MultiChannelStrategy-run
```
