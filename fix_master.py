from app.db import SessionLocal
from app.models import User, Organization, OrganizationMember, MembershipRole
from app.api.auth import get_password_hash

def fix_master():
    db = SessionLocal()
    master = db.query(User).filter(User.email == "master@keepy.com").first()
    if not master:
        print("Master not found, creating...")
        master = User(email="master@keepy.com", hashed_password=get_password_hash("keepy1234"), role="superadmin")
        db.add(master)
        db.flush()
    
    org = db.query(Organization).filter(Organization.slug == "master-org").first()
    if not org:
        print("Creating master org...")
        org = Organization(name="Master Org", slug="master-org")
        db.add(org)
        db.flush()
    
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == master.id, OrganizationMember.org_id == org.id).first()
    if not membership:
        print("Linking master to org...")
        membership = OrganizationMember(user_id=master.id, org_id=org.id, role=MembershipRole.OWNER)
        db.add(membership)
    
    db.commit()
    db.close()
    print("Done")

if __name__ == "__main__":
    fix_master()
