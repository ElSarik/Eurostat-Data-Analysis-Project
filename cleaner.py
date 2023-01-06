import pandas as pd
import numpy as np

from COFOG_scraper import cofog_scrap


def cleaner(dataset_path, gdp_path=None, remove_negative=True, cofog=False, save=False):
    
    # Loading the part of the dataset where the sheet information is located
    information = pd.read_excel(dataset_path,
                                sheet_name = None, skiprows = 3, nrows = 4,
                                usecols = 'A, B, C')

    # Loading the data
    data = pd.read_excel(dataset_path,
                        sheet_name = None, skiprows = 9)

    # Extracting the sheet names from the dataset
    keys = list(information.keys())
    keys.remove('Summary')
    keys.remove('Structure')

    information_sheets = {}
    dataset = pd.DataFrame()

    for key in keys:
        
        df = data[key]
        info_sheet = information[key].T

        # Bringing the sheet information into an appropriate format
        # and storing them into a dictionary
        info_sheet.columns = info_sheet.iloc[0]
        info_sheet.drop(info_sheet.head(2).index,inplace = True)
        info_sheet.reset_index(drop = True, inplace = True)

        information_sheets[key] = info_sheet
        
        # Extracting the category of the information fields
        category_column = info_sheet.columns.values[2]
        category = info_sheet[category_column].iloc[0]

        # Dataset contains some flags, visualized as collumns, which get removed
        df.drop(df.columns[df.columns.str.contains('unnamed',case = False)],axis = 1, inplace = True)

        # Removing the last 5 rows (not needed)
        df.drop(df.tail(5).index,inplace = True)

        # Removing first row since it contains no data
        df.drop(index = 0, inplace = True)

        # Replacing broken header names with their actual name
        df.rename(columns={'TIME': 'Country', 'TIME.1': 'UNIT'}, inplace = True)
        
        
        # Extracting the Year columns
        year_list=list(df.columns)
        year_list.remove('Country')
        year_list.remove('UNIT')

        # Splitting the data based on the measurement unit and also adding the category name
        gdp = df.loc[df['UNIT'] == 'Percentage of gross domestic product (GDP)']
        gdp = pd.melt(gdp, id_vars = ['Country'], value_vars = year_list, var_name = 'Year', value_name = '% GDP', ignore_index=False)
        gdp = gdp.sort_values(by = ['Country', 'Year']).reset_index(drop = True)
        gdp['Category'] = category

        millions = df.loc[df['UNIT'] == 'Million euro']
        millions = pd.melt(millions, id_vars = ['Country'], value_vars = year_list, var_name = 'Year', value_name = 'Million euro', ignore_index=False)
        millions = millions.sort_values(by = ['Country', 'Year']).reset_index(drop = True)

        # Merging the necessary data
        df = millions
        df['% GDP'] = gdp['% GDP']
        df['Category'] = gdp['Category']
        
        df.reset_index(drop = True, inplace = True)
        df.replace(':', np.nan, inplace = True)
        df.replace('European Union - 27 countries (from 2020)', 'European Union', inplace = True)
        df.replace('Euro area - 19 countries  (from 2015)', 'Eurozone', inplace = True)
        df.replace('Germany (until 1990 former territory of the FRG)', 'Germany', inplace = True)

        dataset = pd.concat([dataset, df])
        dataset.reset_index(drop = True, inplace = True)

        
        
    if remove_negative:
        cofog_data = cofog_scrap()
        keys = []

        # dataset = dataset.reset_index()
        dataset['Category'] = dataset['Category'].str.casefold()

        for key in cofog_data.keys():
            cofog_data[key] = [value.lower() for value in cofog_data[key]]
            keys.append(key.lower())


        negatives = dataset[dataset['Million euro'] < 0].reset_index()
        negatives_info = negatives[['Country', 'Year', 'Category']]

        indexes = list(negatives['index'])
        for idx in indexes:
            dataset.loc[(dataset.index == idx),['Million euro', '% GDP']] = 0

        for idx, row in negatives_info.iterrows():
            country = row['Country']
            year = row['Year']
            category = row['Category'].lower()
            division = [key for key, value in cofog_data.items() if category in value][0]

            category_filter = dataset.loc[(dataset['Country'] == country) &
                                              (dataset['Year'] == year) &
                                              (dataset['Category'].isin(cofog_data[division]))] 

            category_total = category_filter['Million euro'].sum()

            dataset.loc[((dataset['Country'] == country) &
                         (dataset['Year'] == year) &
                         (dataset['Category'] == division.lower())),['Million euro']] = category_total


            division_filter = dataset.loc[(dataset['Country'] == country) &
                                          (dataset['Year'] == year) &
                                          (dataset['Category'].isin(keys))]

            total = division_filter['Million euro'].sum()

            dataset.loc[((dataset['Country'] == country) &
                         (dataset['Year'] == year) &
                         (dataset['Category'] == 'total')),['Million euro']] = total
            
    
        
    if gdp_path is not None:
        # Loading the data
        data = pd.read_excel(gdp_path,
                            sheet_name = None, skiprows = 8)

        # Extracting the sheet names from the dataset
        keys = list(data.keys())
        keys.remove('Summary')
        keys.remove('Structure')

        for key in keys:
            df = data[key]

            # Dataset contains some flags, visualized as collumns, which get removed
            df.drop(df.columns[df.columns.str.contains('unnamed',case = False)],axis = 1, inplace = True)

            # Removing the last 5 rows (not needed)
            df.drop(df.tail(5).index,inplace = True)

            # Removing first row since it contains no data
            df.drop(index = 0, inplace = True)

            # Replacing broken header names with their actual name
            df.rename(columns={'TIME': 'Country', 'TIME.1': 'UNIT'}, inplace = True)

            # Extracting the Year columns
            year_list=list(df.columns)
            year_list.remove('Country')

            gdp = pd.melt(df, id_vars = ['Country'], value_vars = year_list, var_name = 'Year', value_name = 'Million GDP', ignore_index=False)

            gdp.reset_index(drop = True, inplace = True)
            gdp.replace(':', np.nan, inplace = True)
            gdp.replace('European Union - 27 countries (from 2020)', 'European Union', inplace = True)
            gdp.replace('Euro area - 19 countries  (from 2015)', 'Eurozone', inplace = True)
            gdp.replace('Germany (until 1990 former territory of the FRG)', 'Germany', inplace = True)

        dataset = dataset.merge(gdp, how='left')
        
        # Updating the %GDP with the new values
        dataset['% GDP'] = (dataset['Million euro'] / dataset['Million GDP']) * 100
    
    
    if cofog:    
        cofog_data = cofog_scrap()
        cofog_df = pd.DataFrame.from_dict(cofog_data, orient='index').T

        divs=list(cofog_df.columns)

        cofog_df = pd.melt(cofog_df, value_vars = divs, var_name = 'Division', value_name = 'Category', ignore_index=False)

        cofog_df = cofog_df[cofog_df.Category.notnull()]
        cofog_df.reset_index(drop = True, inplace = True)  

        dataset['Category'] = dataset['Category'].str.casefold()
        cofog_df['Category'] = cofog_df['Category'].str.casefold()
        cofog_df['Division'] = cofog_df['Division'].str.casefold()
        
        dataset = dataset.merge(cofog_df, on='Category', how='left')
        dataset.Division.fillna(dataset.Category, inplace=True)
        
        if gdp_path is not None:
            dataset = dataset[['Country', 'Year', 'Million euro', '% GDP', 'Million GDP', 'Division', 'Category']]
        else:
            dataset = dataset[['Country', 'Year', 'Million euro', '% GDP', 'Division', 'Category']]
        
    
    if save:
        dataset.to_excel('dataset.xlsx')
    
    dataset.reset_index(drop = True, inplace = True)
    return dataset