# fine_tuning/upload_and_train.py
"""
Upload training data to OpenAI and run fine-tuning.

Usage:
    python -m fine_tuning.upload_and_train
    python -m fine_tuning.upload_and_train --epochs 5
    python -m fine_tuning.upload_and_train --job-id ftjob-abc123  # resume monitoring
"""
import sys
import os
import argparse
import time

# Add project root to sys.path so we can import fine_tuning.config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from openai import OpenAI

from fine_tuning.config import (
    TRAINING_DATA_PATH,
    VALIDATION_DATA_PATH,
    BASE_MODEL,
    MODEL_SUFFIX,
    N_EPOCHS,
)


def upload_file(client: OpenAI, file_path: str) -> str:
    """Upload a JSONL file to OpenAI for fine-tuning.

    Args:
        client: OpenAI client instance.
        file_path: Path to the JSONL file to upload.

    Returns:
        The uploaded file ID.
    """
    print(f"[UPLOAD] Uploading file: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Training data file not found: {file_path}")

    file_size = os.path.getsize(file_path)
    print(f"[UPLOAD] File size: {file_size:,} bytes")

    with open(file_path, "rb") as f:
        response = client.files.create(file=f, purpose="fine-tune")

    file_id = response.id
    print(f"[UPLOAD] Upload complete. File ID: {file_id}")
    return file_id


def create_fine_tuning_job(
    client: OpenAI,
    training_file_id: str,
    validation_file_id: str | None,
    model: str,
    suffix: str,
    epochs: int,
) -> str:
    """Create a fine-tuning job on OpenAI.

    Args:
        client: OpenAI client instance.
        training_file_id: ID of the uploaded training file.
        validation_file_id: ID of the uploaded validation file, or None.
        model: Base model to fine-tune.
        suffix: Suffix for the fine-tuned model name.
        epochs: Number of training epochs.

    Returns:
        The fine-tuning job ID.
    """
    print(f"[TRAIN] Creating fine-tuning job...")
    print(f"[TRAIN]   Base model:      {model}")
    print(f"[TRAIN]   Training file:   {training_file_id}")
    print(f"[TRAIN]   Validation file: {validation_file_id or 'None'}")
    print(f"[TRAIN]   Epochs:          {epochs}")
    print(f"[TRAIN]   Suffix:          {suffix}")

    kwargs = {
        "model": model,
        "training_file": training_file_id,
        "hyperparameters": {"n_epochs": epochs},
        "suffix": suffix,
    }
    if validation_file_id:
        kwargs["validation_file"] = validation_file_id

    job = client.fine_tuning.jobs.create(**kwargs)

    job_id = job.id
    print(f"[TRAIN] Fine-tuning job created. Job ID: {job_id}")
    print(f"[TRAIN] Estimated time: 15-45 minutes for ~500 examples.")
    return job_id


def monitor_job(client: OpenAI, job_id: str) -> None:
    """Poll a fine-tuning job until it completes or fails.

    Checks job status every 30 seconds and prints progress events.

    Args:
        client: OpenAI client instance.
        job_id: The fine-tuning job ID to monitor.
    """
    print(f"\n[MONITOR] Monitoring job: {job_id}")
    print(f"[MONITOR] Polling every 30 seconds. Press Ctrl+C to stop (job continues on OpenAI).\n")

    seen_event_ids: set[str] = set()
    poll_interval = 30
    start_time = time.time()

    while True:
        # Retrieve current job status
        job = client.fine_tuning.jobs.retrieve(job_id)
        status = job.status
        elapsed = time.time() - start_time
        elapsed_min = elapsed / 60

        print(f"[MONITOR] Status: {status} (elapsed: {elapsed_min:.1f} min)")

        # Print new events
        try:
            events = client.fine_tuning.jobs.list_events(
                fine_tuning_job_id=job_id, limit=50
            )
            for event in reversed(list(events.data)):
                if event.id not in seen_event_ids:
                    seen_event_ids.add(event.id)
                    print(f"  [EVENT] {event.message}")
        except Exception as e:
            print(f"  [WARN] Could not fetch events: {e}")

        # Check terminal states
        if status == "succeeded":
            print(f"\n{'=' * 60}")
            print(f"[SUCCESS] Fine-tuning complete!")
            print(f"[SUCCESS] Fine-tuned model ID: {job.fine_tuned_model}")
            print(f"[SUCCESS] Total time: {elapsed_min:.1f} minutes")
            print(f"{'=' * 60}")
            print(f"\nTo use this model, set the model parameter to:")
            print(f"  {job.fine_tuned_model}")
            return

        if status == "failed":
            print(f"\n{'=' * 60}")
            print(f"[FAILED] Fine-tuning job failed.")
            if job.error:
                print(f"[FAILED] Error code:    {job.error.code}")
                print(f"[FAILED] Error message: {job.error.message}")
                if job.error.param:
                    print(f"[FAILED] Error param:   {job.error.param}")
            print(f"{'=' * 60}")
            sys.exit(1)

        if status == "cancelled":
            print(f"\n[CANCELLED] Fine-tuning job was cancelled.")
            sys.exit(1)

        # Wait before next poll
        time.sleep(poll_interval)


def main() -> None:
    """Parse arguments, upload data, create job, and monitor progress."""
    parser = argparse.ArgumentParser(
        description="Upload training data to OpenAI and run fine-tuning."
    )
    parser.add_argument(
        "--data",
        type=str,
        default=str(TRAINING_DATA_PATH),
        help=f"Path to training JSONL file (default: {TRAINING_DATA_PATH})",
    )
    parser.add_argument(
        "--validation",
        type=str,
        default=str(VALIDATION_DATA_PATH),
        help=f"Path to validation JSONL file (default: {VALIDATION_DATA_PATH})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=BASE_MODEL,
        help=f"Base model to fine-tune (default: {BASE_MODEL})",
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default=MODEL_SUFFIX,
        help=f"Model suffix (default: {MODEL_SUFFIX})",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=N_EPOCHS,
        help=f"Number of training epochs (default: {N_EPOCHS})",
    )
    parser.add_argument(
        "--job-id",
        type=str,
        default=None,
        help="Resume monitoring an existing fine-tuning job by ID",
    )

    args = parser.parse_args()

    # Initialize OpenAI client (uses OPENAI_API_KEY env var)
    client = OpenAI()

    # If resuming an existing job, skip upload and go straight to monitoring
    if args.job_id:
        print(f"[RESUME] Resuming monitoring for existing job: {args.job_id}")
        monitor_job(client, args.job_id)
        return

    # Step 1: Upload training file
    print("=" * 60)
    print("Step 1: Uploading training data")
    print("=" * 60)
    training_file_id = upload_file(client, args.data)

    # Step 2: Upload validation file (if it exists)
    validation_file_id = None
    if args.validation and os.path.exists(args.validation):
        print()
        print("=" * 60)
        print("Step 2: Uploading validation data")
        print("=" * 60)
        validation_file_id = upload_file(client, args.validation)
    else:
        print()
        print("=" * 60)
        print("Step 2: No validation file provided or file not found. Skipping.")
        print("=" * 60)

    # Step 3: Create fine-tuning job
    print()
    print("=" * 60)
    print("Step 3: Creating fine-tuning job")
    print("=" * 60)
    job_id = create_fine_tuning_job(
        client=client,
        training_file_id=training_file_id,
        validation_file_id=validation_file_id,
        model=args.model,
        suffix=args.suffix,
        epochs=args.epochs,
    )

    # Step 4: Monitor job progress
    print()
    print("=" * 60)
    print("Step 4: Monitoring fine-tuning progress")
    print("=" * 60)
    monitor_job(client, job_id)


if __name__ == "__main__":
    main()
