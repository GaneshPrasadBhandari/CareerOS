import sys
import os
from datetime import datetime

# --- PATH SETUP ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(ROOT_DIR, 'src'))

# --- IMPORTS ---
from careeros.logic.vector_service import vector_db
from careeros.generation.service import build_grounded_package_v2, write_application_package_v2
from careeros.jobs.schema import JobPost
from careeros.parsing.schema import EvidenceProfile

def run_grounded_generation():
    print("🤖 Starting Grounded Generation Process...")

    # --- CONFIGURATION: SELECT THE CANDIDATE ---
    # Change this to "Ganesh_AI_Architect.pdf" or "Krishna_Manual_QA.pdf" to test others
    target_candidate_file = "Ram_Java_Dev.pdf" 
    target_skills = ["Java", "Python", "SQL"]
    
    print(f"👤 Target Candidate: {target_candidate_file}")
    print("📋 Creating validated Job and Profile objects...")
    
    mock_job = JobPost(
        title="Backend Engineer", 
        company="Tech Corp", 
        description="Looking for Java experts to build APIs.",
        raw_text="Job Description: Needs Java, Python, and SQL."
    )
    
    mock_profile = EvidenceProfile(
        skills=target_skills,
        raw_text=f"Resume data for {target_candidate_file}",
        source_uri=f"data/resumes/{target_candidate_file}",
        parsed_at=datetime.utcnow()
    )

    # --- RETRIEVAL WITH METADATA FILTERING (The P19 Upgrade) ---
    skill_to_chunk_ids = {}
    print(f"🔍 Searching Vector DB ONLY for evidence from {target_candidate_file}...")
    
    for skill in target_skills:
        # We use .query directly on the collection to use the 'where' filter
        results = vector_db.collection.query(
            query_texts=[skill],
            n_results=1,
            where={"source": target_candidate_file} # <--- THIS IS THE FIX
        )
        
        if results['ids'] and len(results['ids'][0]) > 0:
            found_id = results['ids'][0][0]
            skill_to_chunk_ids[skill.lower()] = [found_id]
            print(f"✅ Found evidence for {skill} in {target_candidate_file}")
        else:
            print(f"⚠️  No evidence for '{skill}' found in {target_candidate_file}")

    # --- GENERATION (L4 + L9 Layer) ---
    print(f"✍️  Generating package for {target_candidate_file}...")
    try:
        package_v2 = build_grounded_package_v2(
            profile=mock_profile,
            job=mock_job,
            run_id="run_p19_filtered_test",
            profile_path=f"data/resumes/{target_candidate_file}",
            job_path="data/jobs/job_post_001.json",
            overlap_skills=target_skills,
            skill_to_chunk_ids=skill_to_chunk_ids
        )

        output_path = write_application_package_v2(package_v2)
        
        print("-" * 40)
        print(f"🎉 SUCCESS! Grounded package created for {target_candidate_file}.")
        print(f"📂 Location: {output_path}")
        print(f"📌 Citations Complete: {package_v2.citations_complete}")
        print("-" * 40)

    except Exception as e:
        print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    run_grounded_generation()