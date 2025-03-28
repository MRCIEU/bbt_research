#!python
#!/usr/bin/env python3

#############################################################################################
#The “cycle_learning_variables.py” script
#The script expects the output file from the previous rule (cycle_level_data) as input and will 
#output the machine learning results to defined folder. After the input is read the data split into k-folds
#and learning with k-folds cross validation and ROC is carried out on the data at the cycle level
#############################################################################################

import numpy as np
import pandas as pd
import os
import argparse
from loguru import logger
from pathlib import Path
import matplotlib.pyplot as plt

#from classes.custom_k_fold import CustomKFold
from classes.strat_k_fold import StratKFold
from tools.classifier_roc_cross_val import classifier_roc_cross_val
from tools.classifier_importance import plot_importance
from tools.classifier_importance import shap_explainer

parser = argparse.ArgumentParser(description= "A script to filter data")
parser.add_argument('-i', '--input_file', type=str, required=True, help= 'The input dataset')
parser.add_argument('-k', '--splits', type=int, required=True, help= 'The number of splits')
parser.add_argument('-o', '--output_folder', type=str, required=True, help= 'The output folder')

def cycle_level_learning(INPUT, SPLITS, OUTPUT):
    #reading the data
    logger.info("Reading cycle level variables for learning")
    df = pd.read_csv(INPUT)
    renaming = {#Features derived directly from processed-unstandardised cycle data 
        'Data_Length':'Data length',
        'Next Cycle Difference':'Cycle length',
        'Cycle Completeness':'Recorded period cycle proportion',
        'Curve_by_Data':'Length of the cycle curve',
        'max_of_2_periods':'Temperature of largest three-day period',
        'max_pos_of_2_periods':'Position of temperature of largest three-day period',
        'max_of_3_periods':'Temperature of largest four-day period',
        'max_pos_of_3_periods':'Position of temperature of largest four-day period',
        #Features derived with change-point detection (applied to the processed-unstandardised cycle data)
        'Change Point Day':'Day of temperature change',
        'Change Point Mean Diff':'Diff in temperature before and after temperature change',
        #Features derived with DTW (applied to the processed-standardised cycle data) 
        'cost_with_diff':'DTW distance',
        'path_length_with_diff':'Length of optimal warping path',
        'Expanded_nadir_day':'Nadir day',
        'Expanded_peak_day':'Peak day',
        'Standard_nadir_temp_actual':'Nadir temperature',
        'Standard_peak_temp_actual':'Peak temperature',
        'Expanded_nadir_to_peak':'Time to peak',
        'Standard_low_to_high_temp':'Difference between nadir and peak temperatures'
    }
    df.rename(columns = renaming, inplace=True)
    logger.info("Dataset read")

    print("The length of the dataframe is", len(df))
    
    the_value_counts = df["PCOS"].value_counts()
    print("Counts of the values are \n", the_value_counts)

    #splitting the data into k-folds
    logger.info("Splitting the dataframe into " +str(SPLITS)+ " folds")
    splitted_df = StratKFold(n_splits = SPLITS, df = df, level="Cycle Level").customSplit()
    print("The splits \n", splitted_df[1])

    print(splitted_df[0]["PCOS"].value_counts())
   
    #the splitted data
    df_for_learning = splitted_df[2]

    #create output folder if not exists
    Path(OUTPUT).mkdir(parents=True, exist_ok=True)

    #Empty variables to store data
    mean_fpr = np.linspace(0, 1, 100)
    all_mean_tpr = []
    all_mean_auc = [] 
    all_std_auc = []
    all_tprs_upper = []
    all_tprs_lower = []

    algorithms = ["RFC", "SVM", "LogReg"]
    colors = ["r", "b", "g"]
    fill_colors = ["lightcoral", "lightskyblue", "lightgreen"]

    #This runs the ML using all algorithms
    for alg in algorithms:
        logger.info("Performing "+ alg)
        shap_values, mean_tpr, mean_auc, std_auc, tprs_upper, tprs_lower = classifier_roc_cross_val("Cycle Level", alg, df_for_learning, OUTPUT)
        all_mean_tpr.append(mean_tpr)
        all_mean_auc.append(mean_auc)
        all_std_auc.append(std_auc)
        all_tprs_upper.append(tprs_upper)
        all_tprs_lower.append(tprs_lower)

        shap_explainer("Cycle Level", alg, shap_values, OUTPUT)
    
    #This plots the mean AUCs of the algorithms  
    fig, ax = plt.subplots(figsize=(6, 6)) 
    ax.plot([0,1], [0,1], ls='--')
    for i, mean_tpr in enumerate(all_mean_tpr):
        ax.plot(
            mean_fpr, 
            mean_tpr,
            color=colors[i],
            label=r"Mean ROC (AUC = %0.2f $\pm$ %0.2f)-" % (all_mean_auc[i], all_std_auc[i]) + algorithms[i],
            lw=1.5,
            alpha=0.8,
        )
        ax.fill_between(
            mean_fpr,
            all_tprs_lower[i],
            all_tprs_upper[i],
            color=fill_colors[i],
            alpha=0.2,
            #label=r"$\pm$ 1 std. dev.",
        )
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Mean ROC for Cycle Level Learning')
    plt.legend(loc="lower right")
    filename = "cycle_level_ML.png"
    plt.savefig(os.path.join(OUTPUT, filename))

    # #RFC classifier
    # logger.info("Performing Random Forest Classification")
    # #rfc_importance, explainers, x_tests = classifier_roc_cross_val("Questionnaire Level", "RFC", df_for_learning, OUTPUT)
    # #rfc_importance, shap_values = classifier_roc_cross_val("Cycle Level", "RFC", df_for_learning, OUTPUT)
    # shap_values, mean_tpr, mean_auc, std_auc = classifier_roc_cross_val("Cycle Level", "RFC", df_for_learning, OUTPUT)
    # all_mean_tpr.append(mean_tpr)
    # all_mean_auc.append(mean_auc)
    # all_std_auc.append(std_auc)

    # #RFC SHAP Explainer
    # #shap_explainer("Cycle Level", "RFC", explainers, x_tests, OUTPUT)
    # shap_explainer("Cycle Level", "RFC", shap_values, OUTPUT)
    # #RFC variable importance
    # #shap_file = os.path.join(OUTPUT, "rfc_explainers.pkl")
    # #joblib.dump(shap_values, shap_file)
    # #plot_importance("Questionnaire Level", "RFC Model Importance", rfc_importance, OUTPUT)

    # #SVM classifier
    # logger.info("Performing Support Vector Machine Classification")
    # #svm_importance, explainers, x_tests = classifier_roc_cross_val("Questionnaire Level", "SVM", df_for_learning, OUTPUT)
    # #svm_importance, shap_values = classifier_roc_cross_val("Cycle Level", "SVM", df_for_learning, OUTPUT)
    # shap_values, mean_tpr, mean_auc, std_auc = classifier_roc_cross_val("Cycle Level", "SVM", df_for_learning, OUTPUT)
    # all_mean_tpr.append(mean_tpr)
    # all_mean_auc.append(mean_auc)
    # all_std_auc.append(std_auc)

    # #SVM SHAP Explainer
    # #shap_explainer("Cycle Level", "SVM", explainers, x_tests, OUTPUT)
    # shap_explainer("Cycle Level", "SVM", shap_values, OUTPUT)
    # #SVM variable importance
    # #shap_file = os.path.join(OUTPUT, "svm_explainers.pkl")
    # #joblib.dump(shap_values, shap_file)

    # #plot_importance("Cycle Level", "SVM Model Importance", svm_importance, OUTPUT)

    # #LogReg classifier
    # logger.info("Performing Logistic Regression")
    # #logreg_importance, explainers, x_tests = classifier_roc_cross_val("Questionnaire Level", "LogReg", df_for_learning, OUTPUT)
    # #logreg_importance, shap_values = classifier_roc_cross_val("Cycle Level", "LogReg", df_for_learning, OUTPUT)
    # shap_values, mean_tpr, mean_auc, std_auc = classifier_roc_cross_val("Cycle Level", "LogReg", df_for_learning, OUTPUT)
    # all_mean_tpr.append(mean_tpr)
    # all_mean_auc.append(mean_auc)
    # all_std_auc.append(std_auc)

    # #LogReg SHAP Explainer
    # #shap_explainer("Questionnaire Level", "LogReg", explainers, x_tests, OUTPUT)
    # shap_explainer("Cycle Level", "LogReg", shap_values, OUTPUT)
    # #LogReg variable importance
    # #shap_file = os.path.join(OUTPUT, "logreg_explainers.pkl")
    # #joblib.dump(shap_values, shap_file)
    # #plot_importance("Questionnaire Level", "LogReg Model Importance", logreg_importance, OUTPUT)

    # #DT classifier
    # # logger.info("Performing Decsion Tree Classification")
    # # dt_model = classifier_roc_cross_val("Cycle Level", "DT", df_for_learning, OUTPUT)
    # # #LogReg variable importance
    # # plot_importance("Cycle Level", "DT Model Importance", dt_model.feature_importances_, OUTPUT)


if __name__ == "__main__":
    args = parser.parse_args()
    cycle_level_learning(args.input_file, args.splits, args.output_folder)