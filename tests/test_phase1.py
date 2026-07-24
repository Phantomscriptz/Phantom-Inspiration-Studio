"""Phase 1 test — Script Generation Pipeline.

Run:  python -m tests.test_phase1
"""

import sys
import json
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_ollama_client():
    """Test Ollama connection and model availability."""
    from app.ai.providers.ollama_client import get_client

    print("=" * 60)
    print("TEST 1: Ollama Client Connection")
    print("=" * 60)

    client = get_client()

    if not client.is_alive():
        print("[FAIL] Cannot connect to Ollama. Is it running?")
        print("       Start it with: ollama serve")
        return False

    print("[PASS] Ollama server is running")

    models = client.list_models()
    for m in models:
        print(f"  Model: {m['name']} ({m['details']['parameter_size']})")

    if not client.model_exists("qwen2.5:7b"):
        print("[WARN] qwen2.5:7b not found. Pulling may be needed.")
    else:
        print("[PASS] qwen2.5:7b is available")

    return True


def test_niches():
    """Test available content niches."""
    print()
    print("=" * 60)
    print("TEST 2: Available Content Niches")
    print("=" * 60)

    from app.ai.agents.script_writer import ScriptWriter

    niches = ScriptWriter.available_niches()
    for key, info in niches.items():
        print(f"  {key:<25s} | {info['name']:<30s} | RPM: {info['rpm']}")

    print(f"\n  Total niches: {len(niches)}")
    print("[PASS] All niches loaded")
    return True


def test_short_form_script():
    """Test short-form script generation."""
    print()
    print("=" * 60)
    print("TEST 3: Short-Form Script Generation (30s)")
    print("=" * 60)
    print("  Generating... (this may take 30-60 seconds)")

    from app.ai.agents.script_writer import ScriptWriter

    writer = ScriptWriter(model="qwen2.5:7b")

    try:
        script = writer.write_short_form(
            topic="The most haunted lighthouse in the world",
            niche="scary_stories",
            duration_seconds=30,
        )

        print()
        print(f"  Title:   {script.title}")
        print(f"  Hook:    {script.hook[:100]}...")
        print(f"  Segments: {len(script.segments)}")
        print(f"  Duration: {script.get_total_duration()}s")
        print(f"  CTA:     {script.cta}")
        print(f"  Tags:    {script.hashtags[:5]}")

        print()
        print("  --- NARRATION PREVIEW ---")
        narration = script.get_full_narration()
        print(f"  {narration[:300]}...")
        print()

        # Save to file
        output_dir = Path("projects/_test_output")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "test_short_form.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(script.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"  Saved to: {output_path}")
        print("[PASS] Short-form script generated successfully")
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_metadata_generation():
    """Test metadata generation for YouTube."""
    print()
    print("=" * 60)
    print("TEST 4: Metadata Generation (YouTube)")
    print("=" * 60)
    print("  Generating metadata... (this may take 20-40 seconds)")

    from app.ai.agents.script_writer import ScriptWriter
    from app.ai.models.script import VideoScript, ScriptSegment

    writer = ScriptWriter(model="qwen2.5:7b")

    # Create a mock script for metadata generation
    script = VideoScript(
        title="The Haunted Lighthouse That Keeps Its Light On",
        description="",
        niche="scary_stories",
        format="short_form",
        segments=[
            ScriptSegment(
                scene_number=1,
                narration="There's a lighthouse off the coast of England that has never stopped burning.",
                image_prompt="Dark stormy lighthouse on rocky cliff, lightning in background",
                duration_seconds=10,
            )
        ],
        hook="There's a lighthouse that has never stopped burning — even after everyone who tended it died.",
    )

    try:
        metadata = writer.generate_metadata(script, platform="youtube")

        print()
        print(f"  Title:       {metadata.title}")
        print(f"  Description: {metadata.description[:150]}...")
        print(f"  Hashtags:    {metadata.hashtags[:8]}")
        print(f"  Tags:        {metadata.tags[:8]}")
        print(f"  Thumbnail:   {metadata.thumbnail_prompt[:100]}...")
        print()
        print("[PASS] Metadata generated successfully")
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def main():
    """Run all Phase 1 tests."""
    print()
    print("#" * 60)
    print("#  PHANTOM INSPIRATION STUDIO — Phase 1 Test")
    print("#  Script Generation Pipeline")
    print("#" * 60)
    print()

    results = {}

    # Test 1: Connection
    results["ollama_client"] = test_ollama_client()
    if not results["ollama_client"]:
        print("\n[ABORT] Cannot proceed without Ollama. Exiting.")
        return

    # Test 2: Niches
    results["niches"] = test_niches()

    # Test 3: Short-form script
    results["short_form"] = test_short_form_script()

    # Test 4: Metadata
    results["metadata"] = test_metadata_generation()

    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {test_name}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n  {passed}/{total} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    main()
