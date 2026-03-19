import asyncio
import os
import sys
import numpy as np
from sqlalchemy.future import select
from datetime import datetime, timedelta

# Ensure we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import Story
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans

async def compute_universe():
    print("Beginning Universe Computation...")
    async with SessionLocal() as db:
        now = datetime.utcnow()
        start = now - timedelta(days=90)
        
        print(f"Fetching active stories since {start}...")
        stmt = select(Story).where(Story.is_active == True, Story.created_at >= start, Story.embedding.isnot(None))
        res = await db.execute(stmt)
        stories = res.scalars().all()
        
        if not stories:
            print("No stories found with embeddings.")
            return

        print(f"Loaded {len(stories)} stories. Extracting embeddings map...")
        
        # Build strict parallel arrays for X and story references
        embeddings = []
        valid_stories = []
        for s in stories:
            if isinstance(s.embedding, list) and len(s.embedding) > 0:
                embeddings.append(s.embedding)
                valid_stories.append(s)
                
        if not valid_stories:
            print("Embeddings list was empty after formatting.")
            return
            
        X = np.array(embeddings)
        print(f"Matrix shape: {X.shape}. Running T-SNE dimensionality reduction (1536D -> 2D)...")
        print("This may take a minute or two depending on chunk size...")

        tsne = TSNE(n_components=2, random_state=42, perplexity=30, max_iter=1000)
        X_2d = tsne.fit_transform(X)
        
        # Normalize between -1000 and 1000 to match the 3D space size roughly
        x_min, x_max = X_2d[:, 0].min(), X_2d[:, 0].max()
        y_min, y_max = X_2d[:, 1].min(), X_2d[:, 1].max()
        
        X_2d[:, 0] = (X_2d[:, 0] - x_min) / (x_max - x_min) * 2000 - 1000
        X_2d[:, 1] = (X_2d[:, 1] - y_min) / (y_max - y_min) * 2000 - 1000

        print("T-SNE completed. Running K-Means clustering (12 clusters)...")
        # 12 is a good arbitrary number for color palettes in 3D space
        kmeans = KMeans(n_clusters=12, random_state=42, n_init='auto')
        clusters = kmeans.fit_predict(X_2d)
        
        print("Assignments computed. Updating database...")
        
        for idx, story in enumerate(valid_stories):
            story.universe_x = float(X_2d[idx, 0])
            story.universe_y = float(X_2d[idx, 1])
            story.universe_cluster = int(clusters[idx])
            
        await db.commit()
        print("Database commit successful. Universe is ready.")

if __name__ == "__main__":
    asyncio.run(compute_universe())
