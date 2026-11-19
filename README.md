# ENVIRON712-Ecotox
## EcoTox(&Marley)
Alexa Lavinder, Peyton Smith, & Marley Perry

Initial Question (Week 1): Evaluating freshwater plant mortality as a result of heavy metal exposure from the combustion of fossil fuels. 
As, Pb, Cd, Cu, Hg are the metals of interest. 

Intended Audience: Environmental consultants and fossil fuel industry.   

Due to the scope of the data (revealed during initial cleaning), we changed our research question to the following:

**Research Question: Do regions with higher pesticide use have higher contamination concentrations in surface water?**
Optional, with time we would also look at inaturalist data for the region. 

Intended Audience: Residents worried about the amount of pesticide use in their area, farmers, and pesticide companies. 

The analytical report for this project can be found in the Docs folder of this repository under the title "712 Analytical Report"

Additional data can be accessed 

**Data Dictionary**
  Pesticide_Name: Pesticide that was found in surface water ,
  Water_Year: Year for estimated pesticide use and water sample collection ,
  Result_Value: ug/L concentration of pesticide found in surface water ,
  site_ID: USGS site identification number ,
  drainage_area: Drainage area of the watershed identified in the specified site ,
  county_fips: County identifier code ,
  EPEST_HIGH_KG: Estimated (high) pesticide use in kg ,
  Compound: Pesticide used in the county , 
  Pest_Category: Type of pesticide (herbicide e.g.)

  One row of the pest_water_processed data set represents one sample collection. In this sample collection, the table specifies the year, the pesticide, the pesticide concentration, site information (site ID, county, drainage area), estimated pesticide use within that county, and point geometry of the sample site. 

**Dashboard Change Log**
- added explanatory picture of how to use the interactive map to address fact that in peer feedback felt like hard to understand how to use 
- for the individual pesticide model grouped by pesticide type and include type in label so that can understand trends across pesticide type 
- More detailed explanation of individual pesticide model because felt like it was hard to understand

**Data Reproduction**

Data Sources
- Pesticide Data: https://water.usgs.gov/nawqa/pnsp/usage/maps/county-level/ Dataset of estimated pesticide use by county in agriculture from 2013-2017. It is a USGS dataset and was loaded directly into the dashboard from the website. 
- Water Data: https://www.sciencebase.gov/catalog/item/6712dadfd34eb6a152fc9907 Dataset of pesticides concentrations in USGS stream water samples. We used data only from 2013-2017 even though dataset goes from 2013-2022. The data for water samples was downloaded directly from the website. The data is in the box folder. 
- Site Data: Taken from the same water data website. This allowed us to get which counties each water sample came from and thus match with the pesticide data.
- Pesticide Category Data: Dataset of which pesticide type it was was created by Googling each pesticide type and manually creating a dataset. The data is in the box folder. 
  
Selecting Data
- USGS Stream site pesticide concentrations were joined to a dataset that included the coordinates of each monitoring station, coordinates were then used to identify what county each monitoring sites was in
- Estimated pesticide usage data was joined to USGS streams sites (+ locations) by matching compound, year, and county. Averages were calculated for each pesticide per year for each of the monitoring sites

Data Cleaning 
-Map: For the map the average pesticide use is shown. This is the average across all pesticides and years in the county. The water samples were averaged in the same way
-Analysis: In stations with multiple water samples of the same pesticide in the same year the value was averaged

Logging Data
- Preliminary investigation revealed that data (for both mean estimated pesticide use and water concentration) was very right-skewed. Logging the data resulted in closer-to-normal distributions.  

Linear Regression of Total Pesticides
- A linear regression between average estimated pesticide usage and average stream concentration from 2013-2017 was conducted

Linear Regression of Categorized Pesticides
- A key was created to match each pesticide to its respective category and joined to the dataset. Linear regressions were calculated for each pesticide category (avg. est. pesticide usage vs. avg. stream concentration) from 2013-2017

Multiple Linear Regression
- A multiple linear regression was conducted, normalizing by pesticide name, from 2013-2017 

**Dashboard Access**
https://01a1d157-9b9f-ffc0-0baf-f22435667d08.share.connect.posit.cloud

**AI Use**

AI was used to help format and style the dashboard. 

The prompts used: 
1. How do I style a dashboard to have different colors and symbols for different pesticides and years?
2. How to create popups in a map dashboard?
3. Which package should I use to create an interactive dashboard map?
4. How to create tabs on a dashboard?
5. How to create a graph where can pick different pesticides and display them?

How checked validity: 
We reviewed code based on code seen online to create similar products. Additionally we asked AI to explain code and steps for the dashboard. 
  
