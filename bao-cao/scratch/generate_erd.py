import plantuml

server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')

puml_erd = """@startuml
!pragma layout smetana
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 10
skinparam roundcorner 4
skinparam classFontSize 11
skinparam classFontName Arial
skinparam classFontStyle bold
skinparam arrowColor #444444
skinparam classBorderColor #333333
skinparam classBackgroundColor #FDFDFD

' Custom entity styling
hide circle
hide methods

package "Identity & Social Graph" #F0F4F8 {
  entity "users" as users {
    * id : UUID <<PK>>
    --
    * email : VARCHAR(255) <<UQ>>
    * username : VARCHAR(50) <<UQ>>
    * password_hash : VARCHAR(255)
    full_name : VARCHAR(100)
    bio : TEXT
    university : VARCHAR(150)
    * role : user_role (student, staff, admin, edu_org)
    * is_active : BOOLEAN
    * is_verified : BOOLEAN
    interests : JSONB
    created_at : TIMESTAMPTZ
  }

  entity "user_follows" as user_follows {
    * follower_id : UUID <<PK, FK>>
    * following_id : UUID <<PK, FK>>
    --
    created_at : TIMESTAMPTZ
  }
}

package "Groups & Co-hosting" #F5F0F8 {
  entity "groups" as groups {
    * id : UUID <<PK>>
    --
    * name : VARCHAR(100) <<UQ>>
    description : TEXT
    * privacy : group_privacy (public, private)
    * owner_id : UUID <<FK>>
    custom_form_id : UUID <<FK>>
    allow_member_activities : BOOLEAN
    require_approval : BOOLEAN
    created_at : TIMESTAMPTZ
  }

  entity "group_members" as group_members {
    * id : UUID <<PK>>
    --
    * group_id : UUID <<FK>>
    * user_id : UUID <<FK>>
    * role : group_role (owner, admin, member)
    created_at : TIMESTAMPTZ
  }

  entity "group_join_requests" as group_join_requests {
    * id : UUID <<PK>>
    --
    * group_id : UUID <<FK>>
    * user_id : UUID <<FK>>
    * status : VARCHAR(20)
    form_responses : JSONB
    created_at : TIMESTAMPTZ
  }

  entity "activity_cohosts" as activity_cohosts {
    * id : UUID <<PK>>
    --
    * activity_id : UUID <<FK>>
    * group_id : UUID <<FK>>
    created_at : TIMESTAMPTZ
  }

  entity "activity_cohost_invitations" as activity_cohost_invitations {
    * id : UUID <<PK>>
    --
    * activity_id : UUID <<FK>>
    * host_group_id : UUID <<FK>>
    * invited_group_id : UUID <<FK>>
    * status : VARCHAR(20)
    message : TEXT
    created_at : TIMESTAMPTZ
  }
}

package "Activities & Participation" #F0F8F4 {
  entity "activities" as activities {
    * id : UUID <<PK>>
    --
    * host_id : UUID <<FK>>
    * title : VARCHAR(150)
    description : TEXT
    category : VARCHAR(50)
    location : GEOGRAPHY(POINT, 4326) [PostGIS]
    location_name : VARCHAR(200)
    embedding : VECTOR(768) [pgvector]
    * start_time : TIMESTAMPTZ
    * end_time : TIMESTAMPTZ
    * max_participants : INT
    current_participants : INT
    * privacy : activity_privacy
    require_approval : BOOLEAN
    social_work_days : FLOAT (CTXH)
    group_id : UUID <<FK>>
    custom_form_id : UUID <<FK>>
    trophy_id : UUID <<FK>>
    attendance_mode : VARCHAR(20)
    check_in_code : VARCHAR(64) <<UQ>>
    check_in_radius : INT (m)
    created_at : TIMESTAMPTZ
  }

  entity "join_requests" as join_requests {
    * id : UUID <<PK>>
    --
    * activity_id : UUID <<FK>>
    * user_id : UUID <<FK>>
    * status : request_status
    message : TEXT
    form_responses : JSONB
    attendance_confirmed : BOOLEAN
    responded_at : TIMESTAMPTZ
    created_at : TIMESTAMPTZ
  }

  entity "comments" as comments {
    * id : UUID <<PK>>
    --
    * activity_id : UUID <<FK>>
    * user_id : UUID <<FK>>
    parent_id : UUID <<FK>>
    * content : TEXT
    created_at : TIMESTAMPTZ
  }

  entity "content_likes" as content_likes {
    * id : UUID <<PK>>
    --
    * activity_id : UUID <<FK>>
    * user_id : UUID <<FK>>
    created_at : TIMESTAMPTZ
  }

  entity "custom_forms" as custom_forms {
    * id : UUID <<PK>>
    --
    title : VARCHAR(200)
    description : TEXT
    created_at : TIMESTAMPTZ
  }

  entity "form_fields" as form_fields {
    * id : UUID <<PK>>
    --
    * form_id : UUID <<FK>>
    * label : VARCHAR(200)
    * field_type : field_type
    * is_required : BOOLEAN
    * order : INT
    meta_data : JSONB
  }
}

package "Smart Calendar" #FFF8F0 {
  entity "user_busy_slots" as user_busy_slots {
    * id : UUID <<PK>>
    --
    * user_id : UUID <<FK>>
    * title : VARCHAR(150)
    * recurrence : VARCHAR(20)
    start_datetime : TIMESTAMPTZ
    end_datetime : TIMESTAMPTZ
    day_of_week : INT
    start_time_of_day : TIME
    end_time_of_day : TIME
    valid_from : DATE
    valid_until : DATE
    created_at : TIMESTAMPTZ
  }

  entity "busy_slot_exceptions" as busy_slot_exceptions {
    * id : UUID <<PK>>
    --
    * busy_slot_id : UUID <<FK>>
    * skip_date : DATE
  }

  entity "user_vacation_periods" as user_vacation_periods {
    * id : UUID <<PK>>
    --
    * user_id : UUID <<FK>>
    * title : VARCHAR(100)
    * start_date : DATE
    * end_date : DATE
    created_at : TIMESTAMPTZ
  }
}

package "Gamification & Trophies" #FFFDF0 {
  entity "trophies" as trophies {
    * id : UUID <<PK>>
    --
    * name : VARCHAR(100) <<UQ>>
    description : TEXT
    * points : INT
    icon : VARCHAR(50)
    * creator_id : UUID <<FK>>
    created_at : TIMESTAMPTZ
  }

  entity "user_trophies" as user_trophies {
    * id : UUID <<PK>>
    --
    * user_id : UUID <<FK>>
    * trophy_id : UUID <<FK>>
    activity_id : UUID <<FK>>
    created_at : TIMESTAMPTZ
  }
}

package "Admin, Auditing & Notifications" #FBF0F0 {
  entity "notifications" as notifications {
    * id : UUID <<PK>>
    --
    * user_id : UUID <<FK>>
    actor_id : UUID <<FK>>
    activity_id : UUID <<FK>>
    * type : VARCHAR(50)
    * message : TEXT
    * is_read : BOOLEAN
    created_at : TIMESTAMPTZ
  }

  entity "reports" as reports {
    * id : UUID <<PK>>
    --
    * reporter_id : UUID <<FK>>
    * target_type : VARCHAR(50)
    * target_id : UUID
    * reason : VARCHAR(100)
    description : TEXT
    * status : VARCHAR(50)
    resolved_by : UUID <<FK>>
    admin_note : TEXT
    created_at : TIMESTAMPTZ
  }

  entity "organization_verification_requests" as org_verifications {
    * id : UUID <<PK>>
    --
    * user_id : UUID <<FK>>
    * organization_name : VARCHAR(150)
    faculty : VARCHAR(150)
    document_url : VARCHAR(500)
    * status : verification_status
    reviewed_by : UUID <<FK>>
    reviewed_at : TIMESTAMPTZ
    created_at : TIMESTAMPTZ
  }

  entity "admin_audit_logs" as admin_audit_logs {
    * id : UUID <<PK>>
    --
    actor_id : UUID <<FK>>
    * action : VARCHAR(100)
    * target_type : VARCHAR(50)
    * target_id : UUID
    metadata_json : JSONB
    * created_at : TIMESTAMPTZ
  }
}

' Relationships
users ||--o{ user_follows : "follows (follower)"
users ||--o{ user_follows : "followed by (following)"

users ||--o{ groups : "owns"
groups ||--|{ group_members : "has"
users ||--o{ group_members : "joins"
groups ||--o{ group_join_requests : "receives"
users ||--o{ group_join_requests : "requests"

users ||--o{ activities : "hosts"
groups ||--o{ activities : "organizes"
activities ||--o{ activity_cohosts : "co-hosted with"
groups ||--o{ activity_cohosts : "co-hosts"
activities ||--o{ activity_cohost_invitations : "invites"
groups ||--o{ activity_cohost_invitations : "hosts / invited"

activities ||--o{ join_requests : "has"
users ||--o{ join_requests : "registers"

users ||--o{ comments : "writes"
activities ||--o{ comments : "has"
comments ||--o{ comments : "replies to"
users ||--o{ content_likes : "likes"
activities ||--o{ content_likes : "receives"

custom_forms ||--|{ form_fields : "contains"
activities |o--o| custom_forms : "uses form"
groups |o--o| custom_forms : "uses form"

users ||--o{ user_busy_slots : "schedules"
user_busy_slots ||--o{ busy_slot_exceptions : "excepts"
users ||--o{ user_vacation_periods : "takes"

users ||--o{ trophies : "creates"
users ||--o{ user_trophies : "earns"
trophies ||--o{ user_trophies : "awarded to"
activities |o--o{ user_trophies : "awarded in"
activities |o--o| trophies : "rewards"

users ||--o{ notifications : "receives"
users ||--o{ notifications : "triggers (actor)"
activities |o--o{ notifications : "references"
users ||--o{ reports : "reports"
users ||--o{ reports : "resolves"
users ||--o{ org_verifications : "submits"
users ||--o{ org_verifications : "reviews"
users ||--o{ admin_audit_logs : "performed by"

@enduml"""

puml_file = "scratch/erd_he_thong.puml"
img_file = "Images/erd.png"

with open(puml_file, "w", encoding="utf-8") as f:
    f.write(puml_erd)

print("Sending to PlantUML server...")
data = server.processes(puml_erd)
with open(img_file, "wb") as f:
    f.write(data)

print(f"Successfully generated {img_file} ({len(data)} bytes)")
