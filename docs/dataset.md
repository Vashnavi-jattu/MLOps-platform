# Initial dataset: Iranian Churn

MF-009 selects the **Iranian Churn** dataset from the UCI Machine Learning
Repository for the project's first tabular classification example. The data
comes from an Iranian telecommunications company. The repository describes
3,150 customer records, 13 input features, one churn target, and no missing
values in the published dataset. These are source-reported facts; later data
loading work should still inspect the local file before relying on them.

## Source and license

- Dataset: [Iranian Churn Dataset, UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/563/iranian%2Bchurn%2Bdataset)
- DOI: [10.24432/C5JW3Z](https://doi.org/10.24432/C5JW3Z)
- License: **CC BY 4.0**. The license permits sharing and adaptation, including
  for commercial purposes, provided appropriate credit is given, a link to the
  license is supplied, and changes are indicated.
- Attribution to retain with any redistributed copy: *Iranian Churn Dataset,
  UCI Machine Learning Repository, DOI: 10.24432/C5JW3Z; licensed under
  CC BY 4.0.*

Do not commit a downloaded data file unless a later story explicitly requires
it. Keep the source, license, and attribution with the data wherever it is
stored or redistributed.

## Prediction target and inputs

The prediction target is **`Churn`**, a binary label: `1` means the customer
churned and `0` means the customer did not churn. The 13 input fields are:

| Source field | Meaning |
| --- | --- |
| `Call Failure` | Number of call failures. |
| `Complains` | Whether the customer complained (`0` no, `1` yes). |
| `Subscription Length` | Subscription length in months. |
| `Charge Amount` | Charge category, from `0` (lowest) to `9` (highest). |
| `Seconds of Use` | Total call-use duration in seconds. |
| `Frequency of use` | Number of calls made. |
| `Frequency of SMS` | Number of SMS messages sent. |
| `Distinct Called Numbers` | Number of distinct numbers called. |
| `Age Group` | Age category, coded from `1` (younger) through `5` (older). |
| `Tariff Plan` | Plan code: `1` pay-as-you-go, `2` contractual. |
| `Status` | Account status code: `1` active, `2` non-active. |
| `Age` | Integer field labeled `Age` by the source; the dataset record does not define its units or coding further. |
| `Customer Value` | Customer value measure, as named by the source. |

The source says the feature values summarize the first nine months and the
churn label is measured at the end of month twelve, with a three-month gap.
This timing should be preserved when describing the data and its limitations.
Because the records do not provide a per-customer event date for splitting,
the initial experiment will use a **stratified random 80/20 train/test split**
with random seed **42**. Stratification keeps the target proportions similar
between the two partitions. MF-011 will implement this policy; this document
records the decision only.

## Limitations

This is data from one Iranian telecom provider, so model results may not
generalize to other providers, countries, or time periods. The source's field
definitions for `Age` and `Customer Value` are limited, so these fields should
not be given a more specific interpretation without additional evidence.
