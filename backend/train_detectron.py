from detectron2.data.datasets import register_coco_instances
from detectron2.data import MetadataCatalog

DATASET_ROOT = r"C:\ChartSenseAI\data\ChartSenseAIV3.v2i.coco"

register_coco_instances(
    "charts_train",
    {},
    f"{DATASET_ROOT}/train/_annotations.coco.json",
    f"{DATASET_ROOT}/train/images"
)

register_coco_instances(
    "charts_val",
    {},
    f"{DATASET_ROOT}/valid/_annotations.coco.json",
    f"{DATASET_ROOT}/valid/images"
)

register_coco_instances(
    "charts_test",
    {},
    f"{DATASET_ROOT}/test/_annotations.coco.json",
    f"{DATASET_ROOT}/test/images"
)

print("Datasets registered")
