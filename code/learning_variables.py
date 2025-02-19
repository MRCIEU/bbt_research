#!python
#!/usr/bin/env python3

#############################################################################################
#The “learning_variables.py” script
#The script expects the output file from the previous rule (cycle_level_data) as input and will 
#output the features to a CSV file. After the the input is read the outliers on the peak day 
#are trimmed upto 3 times the std after mean. Outliers on the nadir temp are equally trimmed
#upto 3 times the standard deviation before abd after the mean. Records that have their nadir
#days to be greater than 50 were also trimmed out. Records with the difference between their
#nadirs and peaks days as zero, incomplete cycles (mostly last cycles) and cycles with long data
#lengths are also taken out
#############################################################################################

import numpy as np
import pandas as pd
import os
import argparse
from loguru import logger

from classes.classes import Frames
import tools.tools as tools
import questionnaire_variables.preprocess_quest_tools as preprocess

parser = argparse.ArgumentParser(description= "A script to filter data")
parser.add_argument('-i', '--input_temps', type=str, required=True, help= 'The input temperatures dataset')
parser.add_argument('-j','--input_quest', type=str, required=True, help='The input questionnaire data')
parser.add_argument('-k','--model_cycle', type=str, required=True, help='The model cycle')
parser.add_argument('-o', '--output_temps', type=str, required=True, help= 'The output temperatures dataset')
parser.add_argument('-p', '--output_quest', type=str, required=True, help= 'The output questionnaire dataset')

def the_variables(INPUT_TEMPS, INPUT_QUEST, MODEL_CYCLE, OUTPUT_TEMPS, OUTPUT_QUEST):
    temperatures = pd.read_csv(INPUT_TEMPS) #read the data
    #temperatures_trimmed_out = tools.trimming_for_outliers(temperatures) #trim out outliers at the nadirs and peaks
    ## If I do not use the trimming above, ceycles with more than 9 days will be the length of the temperatures df##

    #temperatures_pcos = temperatures_trimmed_out[temperatures_trimmed_out["PCOS"] != 2] #select users with known PCOS values

    quest = pd.read_csv(INPUT_QUEST)

    logger.info("================User Selection Started==================")

    #From temperature data

    #This counts the current cycles after removing cycles that are less than 10 days and greater than 366 days
    counts = dict(temperatures["PCOS"].value_counts())
    logger.info(f"Cycles with more than 10 days and less than 367 days: {counts}")

    #3 (from cycle level filtering). Cycle completeness - I moved this here from User-Level Filtering (process_quest.py > tools.py > cycle_completeness()) so
    # as to obtain the correct cycle completeness after interpolation (see data_extractor_ss.py > slope_nadir_peak())
    df_complete = temperatures[temperatures["Interpolated Cycle Completeness"] >= 0.4]
    counts = dict(df_complete["PCOS"].value_counts())
    logger.info(f"The complete cycles: {counts}")
    current_users = df_complete["User"].nunique()
    logger.info(f"Number of users with complete cycles: {current_users}")

    #1. Total Users with Questionnaire and Temperature Data
    temperatures_with_quest = df_complete[df_complete["PCOS"] != 3] 
    counts = temperatures_with_quest["User"].nunique()
    logger.info(f"Users with Questionnaire and Temperature Data: {counts}")
    
    #2. Users with answer to Fertility Question
    temperatures_pcos = temperatures_with_quest[temperatures_with_quest["PCOS"] != 2] 
    counts = temperatures_pcos["User"].nunique()
    logger.info(f"Users with answer to Fertility Question: {counts}")

    #3. Users in model cycle
    model_users = Frames(MODEL_CYCLE).model_users()
    non_model = temperatures_pcos[~(temperatures_pcos["User"].isin(model_users))]
    counts = non_model["User"].nunique()
    logger.info(f"Non-model Users: {counts}")
    
    #4. Users with more than 3 Cycles
    more_than_3 = non_model.groupby("User").count()[non_model.groupby("User").count()["Cycle"] > 2]
    more_than_3_list = more_than_3.index.to_list()
    more_than_3_df = non_model[non_model["User"].isin(more_than_3_list)]
    counts = more_than_3_df["User"].nunique()
    logger.info(f"Users with 3 and more cycles: {counts}")
    counts = dict(more_than_3_df["PCOS"].value_counts())
    logger.info(f"Cycles Distribution: {counts}")

    # dep_and_indep = final_df[[
    # "User", "Cycle", "Standard_smooth_temps", "Standard_distance", "Standard_nadir_day", "Standard_peak_day", 
    # "Standard_nadir_temp_actual", "Standard_peak_temp_actual", "Standard_nadir_to_peak", "Standard_low_to_high_temp", 
    # "nadir_valid", "peak_valid", "path_length", "warp_degree", "Curve_Length", "Data_Length", "Curve_by_Data", "PCOS"    
    # ]]

    #5. Questionnaire Missingness (first get users with more than 3 cycles from temps, then get users with less than 3 missing questionnaire varibles 
    # from "BMI", "Regular Smoker", "Age menstration started", "Period in last 3 months", "Regular periods", "Heavy periods", "Painful periods) and preprocessing
    
    #From questionnaire data
    df_quest = quest[quest["User ID"].isin(more_than_3_list)][["User ID", "BMI", "Regular Smoker", "Age menstration started", "Period in last 3 months", "Regular periods", \
                                                       "Heavy periods", "Painful periods", "PCOS"]].reset_index(drop = True)
    
    #6. Users that have had at least a mentruation
    had_menstruation = df_quest[df_quest["Age menstration started"] != "I have not had periods"]
    had_menstruation.reset_index(inplace = True)
    counts = had_menstruation["User ID"].nunique()
    logger.info(f"Users that had menstruation in the past: {counts}")
    
    #missingness in the questionnaire variables (take out users with more than 5 missing values)
    df_missingness = preprocess.get_missing(had_menstruation).reset_index(drop = True)
    
    ##### To ensure imputation for missing values at fold level, i do not not need to imput here. The imputation will be done during the splitting
    #preprocessing and defining categories (missing values imputted to here)
    #df_preprocessed = preprocess.pre_processing_redone(df_missingness)

    ##### Also for creating the dummy variables, is better to do it during splitting becasue of the imputation
    #Get dummy variables
    #dummies = pd.get_dummies(df_missingness[["Regular Smoker", "Period in last 3 months", "Regular periods", "Heavy periods", "Painful periods"]], drop_first=True)
    #df_init = df_preprocessed[["User ID", "BMI", "Age menstration started", "PCOS"]]
    #final_quest_ml = pd.concat([df_init, dummies], axis = 1)
    ###################################
    
    final_quest_ml = df_missingness[["User ID", "BMI", "Age menstration started", "PCOS", "Regular Smoker", "Period in last 3 months", "Regular periods", "Heavy periods", "Painful periods"]]
    final_quest_ml.rename({"User ID":"User"}, axis =1, inplace=True)
    counts = final_quest_ml["User"].nunique()
    logger.info(f"Users in questionnaire data after taking out missingness: {counts}")
    user_counts = dict(final_quest_ml["PCOS"].value_counts())
    logger.info(f"Final Users Distribution: {user_counts}")

    #list of users cleaned from questionnaire
    quest_list = final_quest_ml["User"].to_list()

    # Obtain the questionnare list from the temperature df
    final_temp_df = more_than_3_df[more_than_3_df["User"].isin(quest_list)]
    counts = final_temp_df["User"].nunique()
    logger.info(f"Final users in temperatures data: {counts}")
    
    counts = dict(final_temp_df["PCOS"].value_counts())
    logger.info(f"Final Cycles Distribution: {counts}")

    #An intermediate dataset of the cleaned users dataset for examination of features
    TEMP_SAVE = os.path.join("/".join(OUTPUT_TEMPS.split("/")[:-1]), "final_user_list_before_3_sampling.csv")
    final_temp_df.to_csv(TEMP_SAVE, index=False)
    logger.info(f"Complete Cycle Level Variables: {TEMP_SAVE}")
    #final_temp_df.to_csv("/projects/MRC-IEU/research/projects/ieu2/p6/063/working/data/results/final_user_list_before_3_sampling.csv", index=False)

    logger.info("================User Selection Ended==================")

    #select the independent and non-indepent variables
    dep_and_indep = final_temp_df[[
    "User", "Cycle", "Standard_smooth_temps", "Smooth_Temp", "Data_Length", "Next Cycle Difference", "Cycle Completeness", "Curve_by_Data", 
    "max_of_2_periods", "max_pos_of_2_periods", "max_of_3_periods", "max_pos_of_3_periods", 
    "Change Point Day", "Change Point Mean Diff", 
    "cost_with_diff", "path_length_with_diff", "Standard_nadir_day", "Standard_peak_day", "Expanded_nadir_day", "Expanded_peak_day",
    "Standard_nadir_temp_actual", "Standard_peak_temp_actual", "Standard_nadir_to_peak", "Expanded_nadir_to_peak", "Standard_low_to_high_temp", 
    "PCOS"
    ]]

    #Maintain the "Minimum of 3 Cycles per User" rule
    # less_3 = list(dep_and_indep.groupby("User").count()[dep_and_indep.groupby("User").count()["Cycle"] < 3].index)
    # df_variables =  dep_and_indep[~(dep_and_indep["User"].isin(less_3))]

    #sample 3 cycles each from all users
    #df_3_cycles = tools.select_3_cycles(df_variables)

    df_3_cycles = tools.select_3_cycles(dep_and_indep)

    #save the final result
    df_3_cycles.to_csv(OUTPUT_TEMPS, index=False)
    logger.info(f"Cycle Level Variables of 3 Sampled Cycles per User: {OUTPUT_TEMPS}")

    final_quest_ml.to_csv(OUTPUT_QUEST, index=False)
    logger.info(f"Questionnaire Variables: {OUTPUT_QUEST}")



if __name__ == "__main__":
    args = parser.parse_args()
    the_variables(args.input_temps, args.input_quest, args.model_cycle, args.output_temps, args.output_quest)