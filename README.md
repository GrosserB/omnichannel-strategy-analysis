# Analysis of Omnichannel Marketing Strategy: How Much Do Offline Showrooms Increase Online Sales?
## Summary
This project for a Berlin-based e-commerce firm uses confidential online sales data to estimate the causal effect of offline showrooms on online sales. We employ synthetic control and difference-in-differences methods to estimate the causal parameters. The results of our analyses suggest that a brick-and-mortar showroom increases online sales in the area surrounding the showroom by between 7% and 20%. The numbers are statistically and economically significant; the more credible estimates are at the lower end of that range. In combination with the costs of operating the showrooms, a "showroom ROI" can be obtained and benchmarked against that of other marketing channels. Therefore, this project provides important inputs that support strategic decision-making on the optimal marketing mix.
<br />
<br />

<p align="center">
<img src="./output/KNN_Match_City1.png" width="600" height="400"/>
</p>

  *This chart shows online sales for the areas neighboring a showroom relative to matched control areas where no showroom opened. The online sales for both areas are indexed on the opening year-quarter (green: showroom "city 1", red: KNN-matched areas with no showroom)*

<br>
<br>

**Authors**: <br>
Michael Dietrich ([LinkedIn](https://www.linkedin.com/in/m-dietrich/), [Github](https://github.com/mihyael)) <br>
Benjamin Grosse-Rueschkamp ([LinkedIn](https://www.linkedin.com/in/benjamingrosserueschkamp), [Github](https://github.com/GrosserB)) <br>

**Note**: <br>
The data used for this project is confidential, hence any information shown here that could identify the firm (e.g. showroom location, opening dates, or absolute numbers) are fictionalized. This project page is still work-in-progress. <br>
<br/>

## Table of Contents
- [Project Summary](#summary)
- [Table of Contents](#table-of-contents)
- [Marketing Attribution Objective & Causal Inference Challenge](#marketing-attribution-objective--causal-inference-challenge)
- [Analyses & Results](#analyses--results)
  - [Data Preprocessing](#data-preprocessing)
  - [Event-study Difference-in-Differences with KNN-Matched Control Group](#event-study-difference-in-differences-with-knn-matched-control-group)
  - [Synthetic Control Method](#synthetic-control-method)
  - [Two-Way Fixed-Effects Difference-in-Difference](#two-way-fixed-effects-difference-in-difference)
- [Summary of Results & "So What"](#summary-of-results--so-what)

<br>
<br>

## Marketing Attribution Objective & Causal Inference Challenge

Omnichannel marketing is fast becoming a central pillar in B2C marketing. In particular, e-commerce companies increasingly use brick-and-mortar showrooms to showcase the product physically and thereby provide important information on the product and strengthen brand awareness. Designing an effective marketing strategy requires accurate estimates on the impact of each channel in order to maximize the overall return on marketing spend. Obtaining these estimates for the showroom channel is the objective of this project. <br>

We collaborate with a Berlin-based e-commerce company to analyze and quantify the causal impact of their brick-and-mortar showrooms on online sales. For a sample period of several years, we are provided confidential order data of every order made. Several new showrooms are opened during that time period. The showrooms allow interaction with the products on-site but both order process and fulfillment are online. Conceptually, we solve the marketing attribution problem using methods from the causal inference toolkit. <br>

The challenge is to ensure that we don't misinterpret partial correlations as causal relationships but instead recover as accurately as possible the true underlying parameters. The fundamental idea behind the analysis is to view the opening of new showrooms as a number of geographically separated quasi-experiments. This allows us to construct treatment and control groups. The treatment group contains customers that are geographically close to a newly opened store and thus have some probability of being exposed to the showroom channel. In the control group are locations that further away from showrooms that are less likely to be affected to this marketing channel. <br>

A particular methodological concern in this setting are potentially hidden factors that impact sales and that are also correlated to treatment ("omitted variable bias"). In particular, all showrooms are located in urban areas. However, consumers in urban areas may exhibit differential online shopping behaviors compared to consumers in rural areas even in the absence of treatment. During covid lockdowns, for example,  urban and rural consumer behavior was impacted differently. Therefore, naive comparisons of online sales in areas with showrooms vs. those without, or simple before-after comparisons are likely to be biased and would lead to misleading conclusions. <br>
<br>

<p align="center">
<img src="./output/Pandemic_Growth_by_PopulationDensity.png" width="400" height="400"/>
</p>

*This chart shows online sales growth during the covid-19 pandemic across population density quantiles. More densely populated areas increased their online order volume at a higher rate during the pandemic* <br>
<br>

To tackle these challenges and obtain robust estimates, we employ three state-of-the-art methodologies from the causal inference toolkit: (1) event-study difference-in-differences with k-nearest neigbors to select the control group, (2) synthetic control methods, and (3) heterogenous-robust two-way fixed-effects difference-in-difference estimation methods. <br>
<br>


## Analyses & Results
### Data Preprocessing

We start by cleaning and preprocessing the data. In the time dimension, online sales data is aggregated on the year-quarter level. On the geographic dimension, we aggregate sales data on the postal code level. The location of the showrooms and of the postal codes are geocoded. We then computed the distance between each showroom-postal code pair. We define areas as "treated" if their location is <50km from a showroom that opened during our sample period (some showrooms had opened before). We additionally augment the dataset with the population density (from public sources) and average credit score of the postal code area (provided to us by the e-commerce firm). <br>


### Event-study Difference-in-Differences with KNN-Matched Control Group

First, we use nearest neighbor matching to construct a control group. The purpose of the control group is to provide a counterfactual to the treatment group, i.e., to provide the outcome that would have happened to the treatment group had it not been exposed to the treatment. To obtain the control group, we match each treated each postal code area with two other postal code areas using nearest neighbor matching based on on the variables (i) population density, (ii) average credit quality and (iii) total online sales of the very first time period in our data. In a multivariate regression, these three variables explain about 70% of the cross-sectional variation of the online sales. We match two instead of just one control postal code to each treatment postal code to increase the sample size and thereby reduce the standard errors in our estimation. <br>


<p align="center">
<img src="./output/KNN_Match_City1.png" width="600" height="400"/>
</p>

 *This chart shows online sales for the areas neighboring a showroom relative to matched control areas where no showroom opened. The online sales for both areas are indexed on the opening year-quarter (green: areas around the showroom in "city1", red: KNN-matched areas with no showroom)*

Before the opening of the showroom, online sales grow at similar rates in treatment and control areas. After the showroom opens, the series diverge and the areas around the showroom increase their online order volume at a faster rate. This plot provides first evidence to the effect of the showroom on online sales. <br>

To analyze the effect of the showroom opening more rigorously, we next run an event-style difference-in-differences regression: <br>

<p align="center">
<img src="./output/DiD_City1.png" width="400" height="600"/>
</p>

The table shows the results of the following linear panel regression:<br>

<p align="center">
<img src="https://latex.codecogs.com/svg.image?\inline&space;\small&space;log(order\&space;value_{it})&space;=&space;\alpha&space;&plus;&space;\beta\&space;&space;\mathit{Treatment_i&space;\times&space;Post_t}&space;&plus;&space;\lambda&space;\mathit{Treatment_i}&space;&plus;&space;\phi&space;\mathit{Post_t}&space;&plus;&space;\vartheta&space;&space;X_{it}&space;&plus;&space;\epsilon_{it}"/>
 </p>

This is a classical difference-in-differences regression where the variable *Post* is an indicator variable that equals one for all year-quarters after the showoom opened, and zero otherwise; the variable *Treatment* is an indicator variable that equals one for all postal code areas that are within the 50km range around the showroom, and zero for all control postal code areas. *Treatment* $\times$ *Post* is the interaction term of the two variables, and it the variable of interest. The dependent (aka "target") variable is the natural logarithm of the quarterly total order value (in EUR) in each postal code area. As the dependent variable is logarithmized, we can interpret the parameter estimate on the interaction term *Treatment* $\times$ *Post* as the mean percentage change in the dependent variable for the treated units after the opening of the showroom relative to the untreated postal code areas. Hence, the estimates for the showroom openings show an increase of 10.34%. With a p-value of 0.001, the point estimate is highly statistically significant; standard errors are clustered on the postal-code area. This provides strong evidence for the effect of the showroom, as well as a first estimate of the magnitude of the effect. <br>

The results for the other showrooms are (mostly) similar in magnitude and statistical significance. <br>
<br>

### Synthetic Control Method

We next employ the Synthetic Control Method ("SCM") to analyze the effect of the showroom opening online sales. Similarly to the previous methodology, SCM employs a control group as counterfactual, and uses the Post-treatment periods to estimate the treatment effect. The major difference lies in how the control group is constructed. SCM selects weights to construct a synthetic version of the treated unit such that the outcome in the pre-treatment periods matches the outcome of the treated unit as closely as possible. In contrast to difference-in-differences, only one (aggregate) version of the treated and control unit exists. The treatment effect in absolute numbers is the difference between the treatment area and the synthetic control area. We use the [SyntheticControlMethods](https://github.com/OscarEngelbrektson/SyntheticControlMethods) package to conduct our analysis.

<p align="center">
<img src="./output/SCM_City1.png" width="600" height="400"/>
</p>


In the pre-treatment period, the outcome variable (the mean sales per postal code area) of the synthetic city matches the value of the actual city closely. As the showroom opens the two series diverge visibly, suggesting a positive impact of the showroom on online sales in the area around the showroom. The absolute treatment effect is the difference between the actual value and the synthetic value (note that the EUR values shown on the y-axis are not the actual values). We obtain the percentage change by dividing the average quarterly increase over the 24 months after the showroom opening by the value in the final quarter before treatment. Averaging over the showroom openings in our sample, the analysis suggests an increase of online sales of 20%. <br>
<br>


### Two-Way Fixed-Effects Difference-in-Difference

In the first section we use the canonical (or 'event study'-style) difference-in-differences method. The major limitation of that method is that it can only handle one event at a time and it has no statistically clean way to aggregate the estimates and confidence bands of multiple events. The so-called Two-Way Fixed Effects regression model ("TWFE") is the standard solution to this problem. However, as an emerging scientific literature has pointed out flaws of the original TWFE estimator (under some conditions, e.g., heterogenous or dynamic treatment effects, the estimator delivered biased results), we implement a version of the TWFE estimator that corrects for some of the flaws in the original TWFE estimator introduced by [Callaway & Sant'Anna (2021)](https://www.sciencedirect.com/science/article/abs/pii/S0304407620303948). The [package](https://bcallaway11.github.io/did/articles/did-basics.html) is only available in R so for the analysis we switch to R. <br>
<br>

<p align="center">
<img src="./output/ATT_Aggregated.jpg" width="500" height="350"/>
</p>

 *This chart shows estimates of the __relative__ online sales of the areas surrounding the showrooms compared to areas with not close to a showroom (red: year-quarters before the opening, green: year-quarters after the opening). The dots are the point estimates for each year-quarter and the bars represent 95% confidence intervals. For example, in the first quarter after the opening of a showroom, online sales increase by around 15%. This number is statistically significant on the 95% level (as the zero line is not included in the confidence interval) and is the average for that quarter over all showrooms that opened during our sample period.* <br>

While many of the point estimates are individually not statistically distinguishable from zero, the average of all showroom openings over the entire pre- and post period is. The group-time average treatment effect, i.e. the average sales increase (aggregated over all showroom openings), is 7.4% and is statistically significant at the 0.05-level.  <br>
<br>


## Summary of Results & "So What"

Marketing attribution is the process of identifying which marketing efforts are responsible for generating sales. We investigate the impact of offline showrooms on online sales for a Berlin-based e-commerce company using methods from the causal inference toolkit. Given that different methods require different assumptions, we use three different state of the art quasi-experimental methods (difference-in-differences with KNN-matched control group, synthetic control method, and two-way fixed-effects difference-in-difference) to ensure the robustness of our results. <br>

We find that the effect of offline showrooms on online sales is between 7% and 20%. This range of estimated effects is statistically and economically significant, meaning that the results are unlikely to have occurred by chance and have a material impact on the business. The more credible estimates are at the lower end of the range, suggesting that the true effect of the showroom on online sales is likely to be closer to 7% than to 20%. <br>

Given the estimates, the impact of opening additional showrooms is to be set in relation to the costs to compute the marketing ROI for the showroom channel (outside the scope of this analysis). The showroom channel ROI then needs to be compared to the ROI of alternative marketing strategies, e.g., performance-marketing or direct mail, to determine the ROI-optimal marketing mix. Hence, these results provide insights for the optimization of the company's marketing strategy. <br>
<br>
<br>
