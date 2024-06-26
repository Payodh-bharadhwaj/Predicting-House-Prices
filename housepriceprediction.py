"""# Importing libraries"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.linear_model import RidgeCV, LassoCV
from sklearn.metrics import mean_squared_error as mse
from scipy.stats import skew

# %matplotlib inline

"""# Reading Data"""

curr_path = "/content/drive/My Drive/DSWorkspace/HousePricePrediction"

# read data
train_data = pd.read_csv(curr_path + "/data/train.csv")
test_data = pd.read_csv(curr_path + "/data/test.csv")

"""# Describing Training Data"""

train_data_numeric = train_data.select_dtypes(exclude="object")
train_data_numeric.describe()

train_data_numeric.columns.values

train_data_categorical = train_data.select_dtypes(include="object")
train_data_categorical.columns.values

"""# So we have 43 categorical variables for sure and 37(38 - index) numerical variables, lets find out if all the numerical variables are continous variables?

All categorical variables will be one hot encoded
"""

train_data_numeric.loc[:, train_data.nunique() < 13].columns.values

"""# Oh! So we have 14 categorical variables hidden as numerical values because we see that the above column values have less than 13 unique values in the entire dataset, so these features are categorical features

We will one-hot encode these categorical variables too

# Plots
"""

plt.subplot(122)
plt.xlabel("Lot Area log")
plt.ylabel("SalePrice")
plt.title("Log Lot Area vs SalePrice")
plt.text(10, 700000, "Not Many Outliers Now")
plt.scatter(np.log(train_data["LotArea"]), train_data["SalePrice"])


plt.subplot(121)
plt.xlabel("Lot Area")
plt.ylabel("SalePrice")
plt.title("Lot Area vs SalePrice")
plt.scatter(train_data["LotArea"], train_data["SalePrice"])
plt.text(100000, 600000, "Many Outliers")
plt.subplots_adjust(
    top=0.92, bottom=0.08, left=0.10, right=2.0, hspace=0.25, wspace=0.35
)

to_plot = (
    train_data[["MoSold", "SalePrice"]]
    .copy()
    .groupby("MoSold")
    .mean()
    .apply(lambda x: np.log2(x))
)
plt.subplot(111)
plt.xlabel("Month Sold")
plt.ylabel("SalePrice")
plt.bar(to_plot.index.values, to_plot.values[:, 0])
plt.subplots_adjust(
    top=0.92, bottom=0.08, left=0.10, right=2.0, hspace=0.25, wspace=0.35
)

plt.subplot(121)
plt.xlabel("Index")
plt.ylabel("Sale price")
plt.hist(train_data["SalePrice"])

plt.subplot(122)
plt.xlabel("Index")
plt.ylabel("Log sale price")
plt.hist(np.log1p(train_data["SalePrice"]))
plt.subplots_adjust(
    top=0.92, bottom=0.08, left=0.10, right=2.0, hspace=0.25, wspace=0.35
)

"""Skewness is likely to create bias and hence lets do log transfor so that data is approximately normal and works well with multivariate linear regression"""

plt.subplot(121)
plt.xlabel("Index")
plt.ylabel("Sale price")
plt.scatter(train_data["TotalBsmtSF"], np.log1p(train_data["SalePrice"]))

plt.subplot(122)
plt.xlabel("Index")
plt.ylabel("Log sale price")
plt.scatter(np.log1p(train_data["TotalBsmtSF"]), np.log1p(train_data["SalePrice"]))
plt.subplots_adjust(
    top=0.92, bottom=0.08, left=0.10, right=2.0, hspace=0.25, wspace=0.35
)

plt.subplot(121)
plt.xlabel("Index")
plt.ylabel("Sale price")
plt.hist(train_data["LotArea"])

plt.subplot(122)
plt.xlabel("Index")
plt.ylabel("Log sale price")
plt.hist(np.log1p(train_data["LotArea"]))
plt.subplots_adjust(
    top=0.92, bottom=0.08, left=0.10, right=2.0, hspace=0.25, wspace=0.35
)

plt.subplot(121)
plt.xlabel("Index")
plt.ylabel("Basement Square feet")
plt.hist(train_data["TotalBsmtSF"])

plt.subplot(122)
plt.xlabel("Index")
plt.ylabel("Log Basemetn Square Feet")
plt.hist(np.log1p(train_data["TotalBsmtSF"]))
plt.subplots_adjust(
    top=0.92, bottom=0.08, left=0.10, right=2.0, hspace=0.25, wspace=0.35
)

"""Looks like log transformation of numerical features removes skewness for those variables which are highly skewed."""

# identify cat variables hidden as numerical
# convert categorical variables to dummy variables
# impute missing values using mean
# scale the data using power transformer
# log transform skewed features


def clean_train(train_to_clean):
    cont_vars = train_to_clean.select_dtypes(exclude="object").columns.values
    num_cat_vars = (
        train_to_clean[cont_vars]
        .loc[:, train_to_clean[cont_vars].nunique() < 13]
        .columns.values
    )
    cont_vars = np.array(
        [x for x in cont_vars.tolist() if x not in num_cat_vars.tolist()]
    )

    skewd_feat = train_to_clean[cont_vars].apply(
        lambda x: skew(x, nan_policy="propagate"), axis=0
    )
    skewd_feat = skewd_feat[skewd_feat > 0.7]
    train_to_clean[skewd_feat.index] = np.log1p(train_to_clean[skewd_feat.index])

    cat_vars = train_to_clean.select_dtypes(include="object").columns.values
    cat_vars = np.append(cat_vars, num_cat_vars)
    data_cat = pd.get_dummies(train_to_clean, columns=cat_vars)
    final = data_cat.set_index("Id")
    final = final.groupby(final.columns, axis=1).transform(lambda x: x.fillna(x.mean()))
    return final, skewd_feat


def clean_test(test_to_clean, transformed_train, skewd_feat):
    cont_vars = test_to_clean.select_dtypes(exclude="object").columns.values
    num_cat_vars = (
        test_to_clean[cont_vars]
        .loc[:, test_to_clean[cont_vars].nunique() < 13]
        .columns.values
    )
    cont_vars = np.array(
        [x for x in cont_vars.tolist() if x not in num_cat_vars.tolist()]
    )
    test_to_clean[skewd_feat.index] = np.log1p(test_to_clean[skewd_feat.index])

    cat_vars = test_to_clean.select_dtypes(include="object").columns.values
    cat_vars = np.append(cat_vars, num_cat_vars)
    data_cat = pd.get_dummies(test_to_clean, columns=cat_vars)
    final = data_cat.set_index("Id")
    final = final.groupby(final.columns, axis=1).transform(lambda x: x.fillna(x.mean()))
    final = final.T.reindex(index=transformed_train.columns.values).fillna(0).T
    return final


def fitRidgeCV(train_fit, target, **kwargs):
    train_y = target
    train_x = train_fit
    clf = RidgeCV(**kwargs)
    clf.fit(train_x, train_y)
    print("train loss:{}".format("test"))
    return clf


def predictLassoCV(test_fit, clf):
    return clf.predict(test_fit)


def fitLassoCV(train_fit, target, **kwargs):
    train_y = target
    train_x = train_fit
    clf = LassoCV(**kwargs)
    clf.fit(train_x, train_y)
    print("train loss:{}".format("test"))
    return clf


def predictLassoCV(test_fit, clf):
    return clf.predict(test_fit)


target = np.log1p(train_data["SalePrice"])
train_cleaned, skewd_feat = clean_train(train_data.drop("SalePrice", axis=1))
test_cleaned = clean_test(test_data, train_cleaned, skewd_feat)

ridge_alpha = [
    0.05,
    0.1,
    0.3,
    1,
    3,
    5,
    6,
    7,
    7.5,
    8,
    8.5,
    9,
    10,
    11,
    12,
    15,
    30,
    50,
    75,
    100,
]
train_final = train_cleaned
test_final = test_cleaned
ridgeCV_model = fitRidgeCV(
    train_cleaned, target, normalize=False, alphas=ridge_alpha, store_cv_values=True
)

lasso_alpha = [1, 0.5, 0.1, 0.02, 0.001, 0.0003, 0.0004, 0.0005]
train_final = train_cleaned
test_final = test_cleaned
lassoCV_model = fitLassoCV(
    train_cleaned, target, cv=5, random_state=0, normalize=False, alphas=lasso_alpha
)

"""# Error plots for Ridge cross validation and lasso crossvalidation"""

plt.plot(ridgeCV_model.cv_values_.mean(axis=0))
plt.xlabel("alpha values")
plt.ylabel("mean of Mean squared error of LOOV")
plt.ylim(0, 0.05)
plt.xticks(range(1, len(ridge_alpha) + 1), ridge_alpha)
plt.subplots_adjust(
    top=0.92, bottom=0.08, left=0.10, right=2.0, hspace=0.25, wspace=0.35
)
plt.show()

plt.plot(lassoCV_model.mse_path_)
plt.legend(["cv" + str(i) for i in range(1, lassoCV_model.mse_path_.shape[1] + 1)])
plt.xticks(range(len(lasso_alpha)), lasso_alpha)
plt.xlabel("Alpha value")
plt.ylabel("Test Error")
plt.subplots_adjust(
    top=0.92, bottom=0.08, left=0.10, right=2.0, hspace=0.25, wspace=0.35
)
plt.show()

ridge_output = ridgeCV_model.predict(test_cleaned)

lasso_output = lassoCV_model.predict(test_cleaned)


def writeoutput(output_df, filename, columns, index):
    csv_df = pd.DataFrame(output_df, columns=columns, index=index)
    csv_df.reset_index()
    csv_df.to_csv(filename)
    files.download(filename)


"""# Final Regression Equation and important predictors for House price prediction"""

lasso_coeff_values = lassoCV_model.coef_
lasso_coeff_values = pd.DataFrame(lasso_coeff_values, index=test_cleaned.columns.values)
lasso_coeff_values.sort_values(0)

"""We can see that Low Overall quality index and less pool area negatively effect the sale price of the house
 
 High overall quality rating of 10,9 and neighborhoods of Crawfor and StoneBr are postively associated with high sale prices

# Following code downloads predict sales prices for test data.
"""

writeoutput(
    np.expm1(ridge_output), "ridgecv_output.csv", ["SalePrice"], test_data["Id"]
)

writeoutput(
    np.expm1(lasso_output), "lassocv_output.csv", ["SalePrice"], test_data["Id"]
)

writeoutput(
    lasso_coeff_values.values,
    "Estimated_Coefficient_Values.csv",
    ["values"],
    lasso_coeff_values.index,
)
