# Log book

## 23.11.2026
- [x] Start the project
- [x] Interview with supervisor
- [x] Received ICP data
- [x] Read [AlphaEarth Foundations research paper](docs/2507.22291v2.pdf)
- [x] Watched [Deepmind's conference about AEF](https://www.youtube.com/watch?v=1oiyyIloqxo)
- [x] Found [Google Earth Engine](https://earthengine.google.com/) to manipulate their data

## 24.11.2026
- [x] Registered on Earth Engine
- [x] Imported ICP data and docs
- [x] Project architecture setup
- [x] Set the main objectives
- [x] Pulled and explored the [icp-forest-xai](https://github.com/simlab-vs/icp-forest-xai) repository
- [x] Explored the Earth Engine capabilities

## 25.11.2026
- [~] Follow the Satellite embedding dataset tutorial from Google (NOT COMPLETE)
- [x] Mess with EE and ICP dataset (AEF/ICP_playground.ipynb) to create a first intuition
- [x] goal : have a good understanding on how to integrate them into the project + some plots would be great

## 26.11.2026
- [x] Finish the Satellite embedding dataset tutorial from Google
- [x] Deepen the available data knowledge (intuition + statistical analysis)
- [x] Write a clear list of what data should be kept and what should be pruned
> `cpf-level2_cleaned.parquet` contains only data until end of 2016. Since AEF embeddings start in 2017, there are two choices : 
> 1. switch to the csv files -> have to check for preprocessing;
> 2. don't compare the absolute values but work on differentials -> reduce the time dependence
- [x] Adapted the preprocessing to concatenate datas from csv files

## TODO 27.11.2026
- [x] State report
- [x] Fixed next steps
- [ ] Only load AEF patches related to ICP observation points


## TODO undefined
- [ ] Merge / bind both sides results
- [ ] Align the ICP and AEF data spatially and temporally.
- [ ] Assess correlations between AEF embedding components.
- [ ] Assess relationships AEF embeddings - forest cover + classification model.
- [ ] Assess relationships AEF embeddings - tree species + classification model.
- [ ] Assess relationships (diff) AEF embeddings - defoliation + regression model.
- [ ] Assess relationships (diff) AEF embeddings - growth + regression model.

