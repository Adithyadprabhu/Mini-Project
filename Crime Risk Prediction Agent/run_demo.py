"""
Demonstration script for Predspot: Spatio-temporal crime prediction and hotspot detection.
"""
import time
from predspot import Dataset
from predspot.pipeline import generate_testdata, build_default_pipeline

def main():
    print("=" * 60)
    print("Predspot Demo: Spatio-temporal Crime Prediction Pipeline")
    print("=" * 60)

    # 1. Generate synthetic crime events and study area
    print("\n[1/4] Generating synthetic crime events and study area...")
    start_time = time.time()
    crimes, study_area = generate_testdata(
        n_points=2000,
        start_time="2019-01-01",
        end_time="2020-12-31",
        seed=42,
    )
    print(f"      Generated {len(crimes)} crime events across study area.")
    print(f"      Columns: {list(crimes.columns)}")
    print(f"      Date range: {crimes['t'].min()} to {crimes['t'].max()}")

    # 2. Build Dataset object
    print("\n[2/4] Initializing Predspot Dataset...")
    dataset = Dataset(crimes=crimes, study_area=study_area)
    print("      Dataset initialized successfully.")

    # 3. Build default prediction pipeline
    print("\n[3/4] Building PredictionPipeline (KDE + Feature Engineering + Random Forest)...")
    pipeline = build_default_pipeline(
        study_area=study_area,
        tfreq="M",
        grid_resolution=2.0,  # 2 km grid resolution
        lags=3,
        random_state=42,
    )
    print(f"      Pipeline mapping: {pipeline.mapping}")
    print(f"      Grid points: {len(pipeline.mapping.grid)}")

    # 4. Fit pipeline and predict next period hotspots
    print("\n[4/4] Fitting pipeline on dataset and predicting hotspots...")
    pipeline.fit(dataset)
    print("      Model fit complete.")

    predictions = pipeline.predict()
    print("\nPrediction Results (Next Period Forecast):")
    print("-" * 50)
    print(f"Number of forecast grid locations: {len(predictions)}")
    print("Top 5 predicted hotspot locations:")
    top_hotspots = predictions.sort_values(by="crime_density", ascending=False).head(5)
    for idx, ((period, place), row) in enumerate(top_hotspots.iterrows(), 1):
        print(f"  {idx}. Period {period.strftime('%Y-%m-%d')}, Place {place}: predicted density = {row['crime_density']:.4f}")

    elapsed = time.time() - start_time
    print(f"\nExecution finished successfully in {elapsed:.2f} seconds.")
    print("=" * 60)

if __name__ == "__main__":
    main()
