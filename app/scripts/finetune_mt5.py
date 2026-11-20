"""
finetune_mt5.py — Run on STAGING MACHINE ONLY.

Supervised fine-tuning of mT5-small for Classical Latin translation.
Uses multi-task prefix conditioning for all task types.
Estimated runtime: 8–14 hours (CPU-only); 45–90 minutes (NVIDIA GPU ≥8 GB VRAM).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import torch
import yaml
from datasets import Dataset
from transformers import (
    DataCollatorForSeq2Seq,
    MT5ForConditionalGeneration,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    T5Tokenizer,
)

CONFIG_PATH = Path("config/finetune_config.yaml")


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_jsonl(path: str) -> list[dict]:
    examples = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def tokenise_examples(examples, tokenizer, max_src: int, max_tgt: int):
    model_inputs = tokenizer(
        examples["input_text"],
        max_length=max_src,
        truncation=True,
        padding=False,
    )
    labels = tokenizer(
        text_target=examples["target_text"],
        max_length=max_tgt,
        truncation=True,
        padding=False,
    )
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


def main() -> None:
    config = load_config()
    tc = config["training"]
    dc = config["data"]

    print(f"Loading base model: {config['model_name']}")
    tokenizer = T5Tokenizer.from_pretrained(config["model_name"])
    model = MT5ForConditionalGeneration.from_pretrained(config["model_name"])

    print(f"Loading training data from {dc['train_file']}")
    raw = load_jsonl(dc["train_file"])
    dataset = Dataset.from_list(raw)

    tokenised = dataset.map(
        lambda ex: tokenise_examples(
            ex, tokenizer, tc["max_source_length"], tc["max_target_length"]
        ),
        batched=True,
        remove_columns=dataset.column_names,
    )

    output_dir = config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        num_train_epochs=tc["num_train_epochs"],
        per_device_train_batch_size=tc["per_device_train_batch_size"],
        per_device_eval_batch_size=tc["per_device_eval_batch_size"],
        learning_rate=tc["learning_rate"],
        weight_decay=tc["weight_decay"],
        warmup_steps=tc["warmup_steps"],
        fp16=tc["fp16"],
        gradient_accumulation_steps=tc["gradient_accumulation_steps"],
        save_total_limit=tc["save_total_limit"],
        evaluation_strategy=tc["evaluation_strategy"],
        save_strategy=tc["save_strategy"],
        load_best_model_at_end=tc["load_best_model_at_end"],
        metric_for_best_model=tc["metric_for_best_model"],
        predict_with_generate=True,
        logging_steps=100,
        report_to="none",
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, padding=True)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenised,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    print("Starting fine-tuning...")
    trainer.train()

    final_path = Path(output_dir) / "final"
    final_path.mkdir(exist_ok=True)
    model.save_pretrained(str(final_path))
    tokenizer.save_pretrained(str(final_path))
    print(f"Fine-tuned checkpoint saved to {final_path}")


if __name__ == "__main__":
    main()
