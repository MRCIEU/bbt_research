import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import RocCurveDisplay, auc, roc_curve
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score    

def logreg_classifier(df, OUTPUT_FOLDER):  
    #random_state = np.random.RandomState(0)

    #LogReg
    logmodel = LogisticRegression(C=1, penalty='l1', solver='liblinear')


    tprs = []
    aucs = []
    accs = []

    mean_fpr = np.linspace(0, 1, 100)

    fig, ax = plt.subplots(figsize=(6, 6))

    for fold, data in enumerate(df):
        
        train = data[0]['train']
        test = data[1]['test']
        
        logmodel.fit(train["X_train"], train["y_train"])
        viz = RocCurveDisplay.from_estimator(
            logmodel,
            test["X_test"],
            test["y_test"],
            name=f"ROC fold {fold}",
            alpha=0.3,
            lw=1,
            ax=ax,
            #plot_chance_level=(fold == n_splits - 1),
        )
        
        logreg_pred=logmodel.predict(test["X_test"])
        
        accs.append(accuracy_score(test["y_test"], logreg_pred))
        
        interp_tpr = np.interp(mean_fpr, viz.fpr, viz.tpr)
        interp_tpr[0] = 0.0
        tprs.append(interp_tpr)
        aucs.append(viz.roc_auc)
        
        #get model importance
        importance = logmodel.coef_[0]
        

    mean_tpr = np.mean(tprs, axis=0)
    mean_tpr[-1] = 1.0
    mean_auc = auc(mean_fpr, mean_tpr)
    std_auc = np.std(aucs)
    ax.plot(
        mean_fpr,
        mean_tpr,
        color="b",
        #label=r"Mean ROC (AUC = %0.2f $\pm$ %0.2f)" % (mean_auc, std_auc),
        label=r"Mean ROC (AUC = %0.2f $\pm$ %0.2f)" % (mean_auc, std_auc),
        lw=2,
        alpha=0.8,
    )

    ax.plot([0,1], [0,1], ls='--')

    std_tpr = np.std(tprs, axis=0)
    tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
    tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
    ax.fill_between(
        mean_fpr,
        tprs_lower,
        tprs_upper,
        color="grey",
        alpha=0.2,
        label=r"$\pm$ 1 std. dev.",
    )

    ax.set(
        xlim=[-0.05, 1.05],
        ylim=[-0.05, 1.05],
        xlabel="False Positive Rate",
        ylabel="True Positive Rate",
        title=f"Mean ROC curve with variability-LogReg",
    )
    ax.axis("square")
    ax.legend(loc="lower right")
    plt.savefig(os.path.join(OUTPUT_FOLDER, "LogReg_cycle_level.png"))

    return logmodel
