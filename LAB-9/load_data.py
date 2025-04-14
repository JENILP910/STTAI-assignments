import mlrun
from sklearn.datasets import load_breast_cancer
import pandas as pd

@mlrun.handler(outputs=["dataset", "label_column"])
def breast_cancer_loader(context, format="csv"):

    data = load_breast_cancer(as_frame=True)
    dataset = data.frame
    dataset['target'] = data.target

    context.logger.info('Saving breast cancer dataset to {}'.format(context.artifact_path))
    context.log_dataset('breast_cancer_dataset', df=dataset, format=format, index=False)

    return dataset, "target"

if __name__ == "__main__":
    with mlrun.get_or_create_ctx("breast_cancer_generator", upload_artifacts=True) as context:
        breast_cancer_loader(context, context.get_param("format", "csv"))
