import plantuml

server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')

puml = """@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 9
skinparam roundcorner 4
skinparam classFontSize 10
skinparam classFontName Arial
skinparam classFontStyle bold
skinparam arrowColor #555555
skinparam classBorderColor #444444
skinparam classBackgroundColor #FAFAFA
skinparam linetype ortho

hide circle
hide methods

package "1. Identity & Social Graph" as pkg_users #F0F4F8 {
  entity "users" as users {
    * id : UUID <<PK>>
    --
    * email : VARCHAR(255) <<UQ>>
    * username : VARCHAR(50) <<UQ>>
    * password_hash : VARCHAR(255)
    full_name : VARCHAR(100)
    bio : TEXT
    university : VARCHAR(150)
    * role : user_role
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

package "2. Groups & Co-hosting" as pkg_groups #F5F0F8 {
  entity "groups" as groups {
    * id : UUID <<PK>>
    --
    * name : VARCHAR(100) <<UQ>>
    description : TEXT
    * privacy : group_privacy
    * owner_id : UUID <<FK>>
    custom_form_id : UUID <<FK>>
    allow_member_activities : BOOL
    require_approval : BOOL
    created_at : TIMESTAMPTZ
  }

  entity "group_members" as group_members {
    * id : UUID <<PK>>
    --
    * group_id : UUID <<FK>>
    * user_id : UUID <<FK>>
    * role : group_role
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

package "3. Activities & Forms" as pkg_act #F0F8F4 {
  entity "activities" as activities {
    * id : UUID <<PK>>
    --
    * host_id : UUID <<FK>>
    * title : VARCHAR(150)
    description : TEXT
    category : VARCHAR(50)
    marker_location : POINT (PostGIS)
    meeting_location : VARCHAR(200)
    embedding : VECTOR(768)
    * start_time : TIMESTAMPTZ
    * end_time : TIMESTAMPTZ
    * max_participants : INT
    current_participants : INT
    * privacy : activity_privacy
    require_approval : BOOL
    social_work_days : FLOAT
    group_id : UUID <<FK>>
    custom_form_id : UUID <<FK>>
    trophy_id : UUID <<FK>>
    attendance_mode : VARCHAR(20)
    check_in_code : VARCHAR(64) <<UQ>>
    check_in_radius : INT
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
    attendance_confirmed : BOOL
    responded_at : TIMESTAMPTZ
    created_at : TIMESTAMPTZ
  }

  entity "comments" as comments {
    * id : UUID <<PK>>
    --
    * target_type : VARCHAR(20)
    * target_id : UUID
    * user_id : UUID <<FK>>
    parent_id : UUID <<FK>>
    * content : TEXT
    created_at : TIMESTAMPTZ
  }

  entity "content_likes" as content_likes {
    * id : UUID <<PK>>
    --
    * target_type : VARCHAR(20)
    * target_id : UUID
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
    * is_required : BOOL
    * order : INT
    meta_data : JSONB
  }
}

package "4. Smart Calendar" as pkg_cal #FFF8F0 {
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

package "5. Gamification & Trophies" as pkg_trophies #FFFDF0 {
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

package "6. Admin & Notifications" as pkg_admin #FBF0F0 {
  entity "notifications" as notifications {
    * id : UUID <<PK>>
    --
    * user_id : UUID <<FK>>
    actor_id : UUID <<FK>>
    * type : VARCHAR(50)
    * target_type : VARCHAR(50)
    * target_id : UUID
    * message : TEXT
    * is_read : BOOL
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

' Layout positioning anchors (Top row: Identity, Groups, Activities; Bottom row: Calendar, Gamification, Admin)
user_follows -[hidden]down-> user_busy_slots
group_members -[hidden]down-> trophies
form_fields -[hidden]down-> notifications

' Relationships
users ||--o{ user_follows
users ||--o{ groups
groups ||--|{ group_members
users ||--o{ group_members
groups ||--o{ group_join_requests
users ||--o{ group_join_requests

users ||--o{ activities
groups ||--o{ activities
activities ||--o{ activity_cohosts
groups ||--o{ activity_cohosts
activities ||--o{ activity_cohost_invitations
groups ||--o{ activity_cohost_invitations

activities ||--o{ join_requests
users ||--o{ join_requests

users ||--o{ comments
comments ||--o{ comments
users ||--o{ content_likes

custom_forms ||--|{ form_fields
activities |o--o| custom_forms
groups |o--o| custom_forms

users ||--o{ user_busy_slots
user_busy_slots ||--o{ busy_slot_exceptions
users ||--o{ user_vacation_periods

users ||--o{ trophies
users ||--o{ user_trophies
trophies ||--o{ user_trophies
activities |o--o{ user_trophies
activities |o--o| trophies

users ||--o{ notifications
users ||--o{ reports
users ||--o{ org_verifications
users ||--o{ admin_audit_logs

@enduml"""

data = server.processes(puml)
with open("Images/erd.png", "wb") as f:
    f.write(data)
print("Rendered Images/erd.png successfully:", len(data))
