import numpy as np
import pandas as pd

#getting and defining row and columns missingness levels
def get_missing(df):
    df_values = df.copy()
    
    #for the rows
    df_values["Missing"] = ""
    for i in range(len(df_values)):
        count = 0
        for j in list(df_values.columns):
            if (df_values.loc[i,j] == "Prefer not to answer") | \
            (df_values.loc[i,j] == "No response") | \
            (df_values.loc[i,j] == "Do not know") | \
            (df_values.loc[i,j] == "Don't remember") | \
            (df_values.loc[i,j] == "I don't remember") | \
            pd.isnull(df_values.loc[i,j]):
                count+=1
        df_values.loc[i,"Missing"] = count
    df_values = df_values[df_values["Missing"] < 11] #taking out users with more than 10 missing values
    
    #for the columns
    column_data = []
    for i in list(df_values.columns):
        column_missing = \
        len(df_values[(df_values[i] == "Prefer not to answer") | \
        (df_values[i] =="No response") | \
        (df_values[i] =="Do not know") | \
        (df_values[i] =="Don't remember") | \
        (df_values[i] =="I don't remember") | \
        (pd.isnull(df_values[i]))])

        column_data.append(column_missing)
        
    data = {"Field":list(df_values.columns), "Number Missing":column_data}
    columns_miss = pd.DataFrame(data, columns = ["Field", "Number Missing"])
    
    #return(df_values, columns_miss)
    return(df_values)

#preprocessing and defining categories
def pre_processing(df):
    df_use = df.copy()
    
    #Taking out oulier values
    #df_pro = df_use[~(df_use["BMI"] == "188.1") & ~(df_use["Baby weight (Kg)"] == "28.1")]
    df_pro = df_use

    median_BMI = np.median(df_pro[df_pro["BMI"] != "No response"]["BMI"].astype(float))
    median_sleep_hrs = np.median(df_pro[df_pro["Sleep Hours"] != "No response"]["Sleep Hours"].astype(float))
    median_baby_weight = np.median(df_pro[df_pro["Baby weight (Kg)"] != "No response"]["Baby weight (Kg)"].astype(float))
    #median_menst_age = np.median(df_use[(df_use["Age menstration started"] != "I don't remember") & 
                  #(df_use["Age menstration started"] != "I have not had periods")]["Age menstration started"].astype(float))
    #max_menst_age = np.max(df_use[(df_use["Age menstration started"] != "I don't remember") & 
                  #(df_use["Age menstration started"] != "I have not had periods")]["Age menstration started"].astype(float))


    for i in range(len(df_pro)):
        #imputation for BMI
        if df_pro.iloc[i, 1] == "No response":
            df_pro.iloc[i, 1] = median_BMI

        #imputation for sleep hours
        if df_pro.iloc[i, 3] == "No response":
            df_pro.iloc[i, 3] = median_sleep_hrs    

        #imputation for baby weight
        #if df_pro.iloc[i, 15] == "No response":
            #df_pro.iloc[i, 15] = median_baby_weight

        #categorizing the baby weight
        if (df_pro.iloc[i, 15] == "0.5") | (df_pro.iloc[i, 15] == "1.2") | (df_pro.iloc[i, 15] == "1.5") | \
            (df_pro.iloc[i, 15] == "1.6") | (df_pro.iloc[i, 15] == "1.7") | (df_pro.iloc[i, 15] == "1.8") | \
            (df_pro.iloc[i, 15] == "1.9") | (df_pro.iloc[i, 15] == "2.0") | (df_pro.iloc[i, 15] == "2.1") | \
            (df_pro.iloc[i, 15] == "2.2") | (df_pro.iloc[i, 15] == "2.3") | (df_pro.iloc[i, 15] == "2.4"):
            df_pro.iloc[i, 15] = "Underweight baby"        
        elif (df_pro.iloc[i, 15] == "2.5") | (df_pro.iloc[i, 15] == "2.6") | (df_pro.iloc[i, 15] == "2.7") | \
            (df_pro.iloc[i, 15] == "2.8") | (df_pro.iloc[i, 15] == "2.9") | (df_pro.iloc[i, 15] == "3.0") | \
            (df_pro.iloc[i, 15] == "3.1") | (df_pro.iloc[i, 15] == "3.2") | (df_pro.iloc[i, 15] == "3.3") | \
            (df_pro.iloc[i, 15] == "3.4") | (df_pro.iloc[i, 15] == "3.5") | (df_pro.iloc[i, 15] == "3.6") | \
            (df_pro.iloc[i, 15] == "3.7") | (df_pro.iloc[i, 15] == "3.8") | (df_pro.iloc[i, 15] == "3.9"):
            df_pro.iloc[i, 15] = "Normal weight baby"
        elif (df_pro.iloc[i, 15] == "4.1") | (df_pro.iloc[i, 15] == "4.3") | (df_pro.iloc[i, 15] == "4.4") | \
            (df_pro.iloc[i, 15] == "8.2"):
            df_pro.iloc[i, 15] = "Overweight baby"
        elif (df_pro.iloc[i, 15] == "No response"):
            df_pro.iloc[i, 15] = "No response"
        else:
            df_pro.iloc[i, 15] = "No response"
            
        #categorizing the menstruation age
        if (df_pro.iloc[i, 16] == "6") | (df_pro.iloc[i, 16] == "7") | (df_pro.iloc[i, 16] == "8") | \
            (df_pro.iloc[i, 16] == "9") | (df_pro.iloc[i, 16] == "10"):
            df_pro.iloc[i, 16] = "Early Menstruation Age"
        elif (df_pro.iloc[i, 16] == "11") | (df_pro.iloc[i, 16] == "12") | (df_pro.iloc[i, 16] == "13") | \
            (df_pro.iloc[i, 16] == "14") | (df_pro.iloc[i, 16] == "15"):
            df_pro.iloc[i, 16] = "Normal Menstruation Age"
        elif (df_pro.iloc[i, 16] == "16") | (df_pro.iloc[i, 16] == "17"):
            df_pro.iloc[i, 16] = "Late Menstruation Age"
        elif (df_pro.iloc[i, 16] == "18") | (df_pro.iloc[i, 16] == "19") | (df_pro.iloc[i, 16] == "20") | \
            (df_pro.iloc[i, 16] == "28"):
            df_pro.iloc[i, 16] = "Very Late Menstruation Age"
        elif (df_pro.iloc[i, 16] == "I have not had periods"):
            df_pro.iloc[i, 16] = "I have not had periods"
        elif (df_pro.iloc[i, 16] == "I don't remember"):
            df_pro.iloc[i, 16] = "I don't remember"
        else:
            df_pro.iloc[i, 16] = "No response"
    
    return df_pro