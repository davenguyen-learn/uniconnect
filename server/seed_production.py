"""
Production seed script — large-scale realistic Vietnamese university data.

Target: 300+ rows per entity type.
Approach: Combinatorial generation from pools of names, templates, locations.

Creates:
  • 1   admin user
  • 300 students across 10 real Vietnamese universities
  • 300 student groups
  • 350 activities with real geo-coordinates across Vietnam
  • 600+ follow relationships
  • 900+ group memberships
  • 500+ join requests
  • 300+ comments + 100+ replies
  • 500+ content likes
  • 300 documents
  • 300 notifications
  • 300 reports

Run:
  $env:DATABASE_URL = "postgresql+asyncpg://..."
  python seed_production.py
"""

import asyncio
import datetime
import itertools
import random
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.modules.users.models import User, UserRole, UserFollow
from app.modules.groups.models import Group, GroupMember, GroupRole
from app.modules.activities.models import Activity, ActivityPrivacy
from app.modules.participation.models import JoinRequest, RequestStatus
from app.modules.documents.models import Document
from app.modules.interactions.models import Comment, ContentLike
from app.modules.notifications.models import Notification
from app.modules.reports.models import Report


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA POOLS — combinatorial building blocks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UNIVERSITIES = [
    ("Đại học Bách khoa Hà Nội", "hust"),
    ("Đại học Quốc gia Hà Nội", "vnu"),
    ("Đại học Kinh tế Quốc dân", "neu"),
    ("Đại học Bách khoa TP.HCM", "hcmut"),
    ("Đại học FPT", "fpt"),
    ("Đại học Sư phạm Hà Nội", "hnue"),
    ("Đại học Ngoại thương", "ftu"),
    ("Đại học Công nghệ - ĐHQGHN", "uet"),
    ("Đại học Tôn Đức Thắng", "tdtu"),
    ("Đại học RMIT Việt Nam", "rmit"),
]

LAST_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ",
    "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đào", "Đinh", "Lưu", "Mai",
]

MIDDLE_NAMES = [
    "Văn", "Thị", "Hoàng", "Minh", "Thanh", "Đức", "Anh", "Hữu", "Quốc",
    "Ngọc", "Thuỳ", "Phương", "Bảo", "Gia", "Hồng", "Thu", "Khánh", "Tiến",
    "Tường", "Kiều", "Mỹ", "Trọng", "Hà", "Thành",
]

FIRST_NAMES = [
    "Minh", "Linh", "Hùng", "Hà", "Tuấn", "Mai", "Đức", "Thảo", "Khánh", "An",
    "Long", "Phương", "Nam", "Hiền", "Sơn", "Hương", "Quang", "Vy", "Đạt", "Chi",
    "Huy", "Trang", "Tài", "Nhi", "Phúc", "Thy", "Khoa", "Uyên", "Duy", "Hạnh",
    "Trung", "Hoa", "Bảo", "Ngọc", "Thành", "Vi", "Dũng", "Lan", "Hiếu", "My",
    "Vinh", "Nhung", "Tâm", "Giang", "Khôi", "Thuỷ", "Kiên", "Yến", "Đăng", "Trinh",
]

BIO_TEMPLATES = [
    "SV {major} K{k} {uni}. {hobby}.",
    "{major} {uni}. Đam mê {interest}. {extra}.",
    "Sinh viên năm {year} ngành {major}. {hobby}.",
    "{role} tại {uni}. {interest} enthusiast. {extra}.",
    "K{k} {major}. {hobby}. Đang {doing}.",
    "{uni} - {major}. {extra}. {hobby}.",
]

MAJORS = [
    "CNTT", "Khoa học Máy tính", "Kỹ thuật Phần mềm", "Trí tuệ Nhân tạo",
    "Điện tử Viễn thông", "Cơ khí", "Kiến trúc", "Quản trị Kinh doanh",
    "Tài chính - Ngân hàng", "Marketing", "Kế toán", "Kinh tế Quốc tế",
    "Luật", "Báo chí", "Sư phạm Toán", "Sư phạm Tiếng Anh",
    "Toán Tin ứng dụng", "Vật lý Kỹ thuật", "Kỹ thuật Hoá học",
    "An toàn Thông tin", "Khoa học Dữ liệu", "IoT & Hệ thống nhúng",
    "Thiết kế Đồ hoạ", "Quản lý Công nghiệp", "Logistics",
]

HOBBIES = [
    "Thích code backend và uống cà phê đen",
    "Mê đọc sách và chơi guitar acoustic",
    "Chạy bộ mỗi sáng, target marathon",
    "Photographer nghiệp dư, chuyên chụp phố phường",
    "Mê game và esports, rank Immortal Valorant",
    "Thích nấu ăn và thử món mới mỗi tuần",
    "Chơi bóng rổ 3v3 cuối tuần",
    "Đam mê du lịch bụi, đã đi 20 tỉnh VN",
    "Yêu thích thiên văn học, hay đi ngắm sao",
    "Tập gym 5 buổi/tuần, theo dõi dinh dưỡng",
    "Mê boardgame và DnD",
    "Vẽ tranh digital, nhận commission trên Fiverr",
    "Thích đạp xe quanh thành phố buổi sáng",
    "Chơi piano từ năm 8 tuổi",
    "Thích podcast về tech và startup",
    "Xem phim và viết review trên Letterboxd",
    "Đọc manga và xem anime",
    "Yoga và thiền mỗi sáng",
    "Nuôi 2 con mèo tên Mochi và Pudding",
    "Thích cắm trại và hiking cuối tuần",
]

INTERESTS = [
    "machine learning", "web development", "mobile apps", "cloud computing",
    "blockchain", "game development", "UX/UI design", "competitive programming",
    "fintech", "cybersecurity", "robotics", "data science", "open source",
    "startup", "photography", "content creation", "digital marketing",
    "DevOps", "embedded systems", "NLP và chatbot",
]

EXTRAS = [
    "Intern tại FPT Software", "Freelancer front-end", "Research assistant tại lab AI",
    "Cộng tác viên VnExpress", "Co-founder startup edtech", "Mentor cho SV năm nhất",
    "IELTS 7.5", "JLPT N2", "AWS Certified", "Kaggle Expert",
    "Thành viên AIESEC", "Trưởng ban truyền thông CLB", "Đội trưởng đội project",
    "Content creator 10k followers", "Admin group học tập 5k members",
    "Từng đi exchange tại Hàn Quốc", "Đang học thạc sĩ song song",
    "Google DSC Lead", "Giải nhì ACM-ICPC khu vực",
    "Tình nguyện viên Mùa hè xanh 3 năm liên tiếp",
]

DOINGS = [
    "tìm thực tập hè 2026", "làm đồ án cuối kỳ", "ôn thi IELTS",
    "xây side project", "học React Native", "chuẩn bị thi cuối kỳ",
    "apply master ở Đức", "tìm đồng đội hackathon", "viết blog tech",
    "học tiếng Nhật", "nghiên cứu về LLM", "xây portfolio website",
]

# ── Locations with real GPS coordinates ──
HANOI_LOCATIONS = [
    (21.0045, 105.8442, "Đại học Bách khoa Hà Nội"),
    (21.0383, 105.7828, "Đại học Quốc gia Hà Nội - Xuân Thuỷ"),
    (21.0008, 105.8427, "Đại học Kinh tế Quốc dân"),
    (21.0378, 105.7825, "Sân vận động Mỹ Đình"),
    (21.0285, 105.8542, "Hồ Hoàn Kiếm"),
    (21.0132, 105.8535, "The Coffee House - Bà Triệu"),
    (21.0050, 105.8450, "Thư viện Tạ Quang Bửu"),
    (21.0350, 105.8340, "Highlands Coffee - Cầu Giấy"),
    (21.0227, 105.8195, "Công viên Nghĩa Đô"),
    (21.0082, 105.8469, "KTX Bách khoa"),
    (21.0165, 105.8521, "Bách Khoa Innovation Hub"),
    (21.0298, 105.8521, "Vincom Bà Triệu"),
    (21.0451, 105.7913, "Sân bóng rổ ĐH Quốc gia"),
    (21.0278, 105.8342, "Phố Tạ Quang Bửu"),
    (21.0196, 105.8585, "Co-working Space Toong - Minh Khai"),
    (21.0313, 105.8496, "Phố đi bộ Hoàn Kiếm"),
    (21.0590, 105.7946, "Aeon Mall Hà Đông"),
    (21.0175, 105.8237, "Đại học Ngoại thương HN"),
    (21.0484, 105.8000, "Sân bóng Cầu Giấy"),
    (21.0034, 105.8204, "Học viện Kỹ thuật Quân sự"),
    (21.0288, 105.8028, "Sân FPT Cầu Giấy"),
    (21.0365, 105.8345, "Quán Cộng Coffee - Tây Hồ"),
    (21.0680, 105.8180, "Hồ Tây"),
    (21.0156, 105.8391, "Bệnh viện Bạch Mai"),
    (21.0422, 105.8165, "Lotte Center Hà Nội"),
]

HCMC_LOCATIONS = [
    (10.8800, 106.8057, "Đại học Bách khoa TP.HCM"),
    (10.8481, 106.7720, "ĐH FPT TP.HCM"),
    (10.8520, 106.6291, "Nhà Văn hoá Sinh viên"),
    (10.7769, 106.7009, "Landmark 81"),
    (10.7626, 106.6602, "Công viên Gia Định"),
    (10.8502, 106.7719, "The Workshop Coffee"),
    (10.8792, 106.8065, "KTX ĐHQG HCM"),
    (10.7730, 106.6956, "Phố đi bộ Nguyễn Huệ"),
    (10.8030, 106.7145, "Sân cầu lông Bình Thạnh"),
    (10.8580, 106.7870, "Thư viện ĐH Quốc gia HCM"),
    (10.7580, 106.6820, "ĐH Tôn Đức Thắng"),
    (10.7290, 106.6958, "ĐH RMIT Việt Nam"),
    (10.8710, 106.8020, "Innovation Hub Q9"),
    (10.8020, 106.6340, "Aeon Mall Bình Tân"),
    (10.8481, 106.6352, "Crescent Mall Q7"),
    (10.7876, 106.7052, "Takashimaya Saigon Centre"),
    (10.8450, 106.7690, "Sân bóng ĐH KHTN"),
    (10.8330, 106.6780, "Suất Quán Coffee - Gò Vấp"),
    (10.8020, 106.7520, "Thảo Cầm Viên"),
    (10.7950, 106.7220, "Bến Thành Market"),
]

DANANG_LOCATIONS = [
    (16.0544, 108.2022, "ĐH Bách khoa Đà Nẵng"),
    (16.0718, 108.2230, "Bãi biển Mỹ Khê"),
    (16.0474, 108.2173, "Cầu Rồng"),
    (16.0680, 108.2100, "Co-working Enouvo - Đà Nẵng"),
    (16.0590, 108.2450, "Vincom Plaza Đà Nẵng"),
]

ALL_LOCATIONS = HANOI_LOCATIONS + HCMC_LOCATIONS + DANANG_LOCATIONS

# ── Activity templates: (category, title_template, desc_template) ──
ACTIVITY_TEMPLATES = {
    "Study": [
        ("Ôn thi {subject} - {detail}", "Cùng nhau ôn tập {detail_desc}. Mang theo bài tập và đề thi cũ nhé!"),
        ("Workshop: {tech_topic}", "Hướng dẫn từ cơ bản đến nâng cao. Hands-on workshop thực hành trực tiếp."),
        ("Paper Reading: {paper}", "Đọc và thảo luận paper. Yêu cầu: đọc trước paper, chuẩn bị 2-3 câu hỏi."),
        ("Luyện {lang_skill}", "Practice cùng nhau. Feedback lẫn nhau. Mọi trình độ."),
        ("Group study: {subject}", "Luyện bài tập cùng nhau. Chủ đề tuần này có sẵn trong group chat."),
        ("Seminar: {tech_topic}", "Chia sẻ kinh nghiệm và kiến thức thực tiễn. Q&A sau phần trình bày."),
        ("Code review dự án {project}", "Mang laptop + source code. Cùng review, tìm bug, cải thiện."),
        ("Hướng dẫn {tech_topic} cho người mới", "Step-by-step từ zero. Không cần kinh nghiệm trước."),
        ("Mock interview: {interview_type}", "Luyện phỏng vấn giả lập. Feedback chi tiết sau mỗi vòng."),
        ("Thảo luận sách: {book}", "Đọc và thảo luận. Chia sẻ takeaway cá nhân."),
    ],
    "Sports": [
        ("Chạy bộ {distance} quanh {place}", "Tập hợp 5h30 sáng. Warm-up + chạy + cool down. Pace thoải mái."),
        ("Đánh cầu lông cuối tuần", "Thuê sân 2 tiếng. Mọi trình độ. Chia đội đánh đôi."),
        ("Bóng rổ 3v3 chiều thứ {day}", "Sân ngoài trời. Tìm thêm người đủ đội. Mang theo nước uống."),
        ("Yoga buổi sáng", "Giãn cơ + thiền 45 phút. Mang thảm yoga. Phù hợp beginner."),
        ("Đạp xe {route}", "Khởi hành 6h sáng. Đường bằng phẳng, dễ đạp. Mang mũ bảo hiểm."),
        ("Bơi lội tại {pool}", "Bơi tự do 1 tiếng. Có người hướng dẫn cho ai chưa biết bơi."),
        ("Futsal giao hữu {match}", "Đội nhà vs đội khách. Cổ vũ nhiệt tình! Có nước miễn phí."),
        ("Hiking {mountain}", "Chuẩn bị giày trekking, nước 2L, đồ ăn nhẹ. Xuất phát sớm."),
        ("Tennis đôi cuối tuần", "Sân tennis đất nện. 2 tiếng. Level intermediate+."),
        ("Gym session cùng nhau", "Chest + Triceps day. Có PT hướng dẫn free cho newbie."),
    ],
    "Social": [
        ("Coffee chat: {chat_topic}", "Ngồi cà phê trao đổi kinh nghiệm. Mọi người đều welcome!"),
        ("Giao lưu {social_type}", "Gặp gỡ, networking, games team-building. Đừng ngại đi một mình!"),
        ("Movie night: {movie}", "Cùng xem phim và thảo luận. Bắp rang + nước ngọt có sẵn."),
        ("Potluck dinner - {food_theme}", "Mỗi người mang một món. Ăn uống + giao lưu văn hoá."),
        ("Board game night: {game}", "Mang boardgame hoặc dùng chung. Thời gian chơi ~3 tiếng."),
        ("Birthday party tháng {month}", "Happy birthday! Có bánh kem + quà nhỏ + mini game."),
        ("Networking: {network_topic}", "Anh chị đi trước chia sẻ kinh nghiệm. Q&A thoải mái."),
        ("Photowalk {photo_place}", "Dạo phố + chụp ảnh. Gặp nhau tại điểm hẹn lúc 3pm."),
        ("Karaoke night", "Phòng VIP cho 15 người. Hát từ 7pm. Đặt phòng trước rồi nhé."),
        ("Picnic cuối tuần tại {park}", "Mang đồ ăn + thảm. Chơi đàn guitar + trò chuyện."),
    ],
    "Gaming": [
        ("Giải {game_title} sinh viên", "Đăng ký theo đội. Giải thưởng: voucher + áo team custom."),
        ("Minecraft server cùng xây - Season {season}", "Server SMP. Survival mode. Join Discord để lấy IP."),
        ("League of Legends: Clash {clash}", "Tìm đồng đội rank Gold+. Voice chat Discord."),
        ("Game dev showcase #{num}", "Demo game đồ án. Unity/Unreal/Godot. Vote game hay nhất."),
        ("Chess tournament sinh viên", "Cờ vua nhanh 10 phút. Swiss system. Giải thưởng cho top 3."),
        ("LAN party: {lan_game}", "Mang laptop đến. Đấu 1v1 và team. Có snacks."),
    ],
    "Volunteer": [
        ("Dạy {teach_subject} cho trẻ em", "Dạy miễn phí tại trung tâm cộng đồng. 2 tiếng/buổi."),
        ("Dọn rác {clean_place}", "Nhặt rác + phân loại. Găng tay + túi rác được cung cấp."),
        ("Quyên góp {donate_item}", "Thu gom và gửi lên vùng cao cho các em nhỏ."),
        ("Hiến máu nhân đạo tại {blood_place}", "Khám sức khoẻ miễn phí + quà tặng."),
        ("Trồng cây xanh tại {green_place}", "Mỗi người trồng 1 cây. Dụng cụ có sẵn."),
        ("Nấu cơm từ thiện", "Nấu 200 suất cơm cho người vô gia cư. Cần 15 tình nguyện viên."),
    ],
}

# Fill-in pools for activity templates
SUBJECTS = [
    "Giải tích 2", "Xác suất thống kê", "Đại số tuyến tính", "Vật lý đại cương",
    "Cấu trúc dữ liệu", "Mạng máy tính", "Cơ sở dữ liệu", "Hệ điều hành",
    "Lý thuyết đồ thị", "Kinh tế vi mô", "Kinh tế vĩ mô", "Quản trị học",
    "Tiếng Anh B2", "Tiếng Nhật N3", "Triết học Mác-Lênin", "Pháp luật đại cương",
]

TECH_TOPICS = [
    "Git & GitHub", "Docker & Kubernetes", "React Hooks", "FastAPI", "TypeScript",
    "Machine Learning cơ bản", "CI/CD Pipeline", "GraphQL", "Redis & Caching",
    "Microservices", "Flutter", "Next.js 14", "PostgreSQL nâng cao", "AWS Lambda",
    "Figma cho Developer", "System Design", "TDD với Python", "Rust cho Beginner",
    "Vue.js 3 Composition API", "Spring Boot", "MongoDB", "Nginx & Load Balancing",
    "WebSocket real-time", "OAuth2 & JWT", "LangChain + LLM", "Prompt Engineering",
]

PAPERS = [
    "Attention Is All You Need", "BERT", "GPT-4 Technical Report", "ResNet",
    "YOLO v8", "Stable Diffusion", "AlphaFold", "CLIP", "Segment Anything",
    "LLaMA 3", "DeepSeek Coder", "Mamba: Linear-Time Sequence Modeling",
]

BOOKS = [
    "Clean Code", "The Pragmatic Programmer", "Design Patterns", "System Design Interview",
    "Atomic Habits", "Deep Work", "Sapiens", "Zero to One", "The Lean Startup",
    "Thinking, Fast and Slow", "Hoàng tử bé", "Đắc Nhân Tâm",
]

PROJECTS = ["cuối kỳ", "OOP", "web app", "mobile app", "IoT", "AI/ML", "capstone", "hackathon"]
INTERVIEW_TYPES = ["Frontend", "Backend", "Data Engineer", "PM", "Consulting", "Big4"]
DISTANCES = ["5K", "3K", "10K", "7K"]
ROUTES = ["quanh Hồ Tây", "từ BK đến Hoàn Kiếm", "quanh hồ Linh Đàm", "dọc sông Sài Gòn", "vòng quanh Thủ Thiêm"]
POOLS = ["bể bơi ĐH Bách khoa", "bể bơi Tăng Bạt Hổ", "hồ bơi Phú Thọ", "bể bơi KTX"]
MOUNTAINS = ["Ba Vì", "Tam Đảo", "Tà Năng - Phan Dũng", "Fansipan", "Bạch Mã", "Langbiang"]
MATCHES = ["BK vs ĐH Quốc gia", "FPT vs NEU", "HCMUT vs TDTU", "liên trường mùa xuân"]
MOVIES = ["Interstellar", "Oppenheimer", "Dune 2", "Parasite", "Your Name", "Spider-Verse", "Inside Out 2"]
CHAT_TOPICS = [
    "Kinh nghiệm thực tập", "Career path trong IT", "Du học Úc/Đức/Nhật",
    "Startup từ đại học", "Freelance cho SV", "Học bổng 100%",
    "Chuyện đi làm đầu đời", "Gap year có nên không", "Xây personal brand",
]
SOCIAL_TYPES = ["sinh viên liên trường", "SV năm nhất", "alumni & SV", "CLB cùng trường"]
FOOD_THEMES = ["Ẩm thực miền Bắc", "Món Huế", "Street food Sài Gòn", "Đồ ăn Hàn Quốc", "Món chay"]
GAMES_BOARD = ["Catan", "Avalon", "Codenames", "Uno", "Splendor", "Dixit", "Werewolf"]
PARKS = ["công viên Thống Nhất", "Nghĩa Đô", "Gia Định", "23/9", "Lê Văn Tám"]
PHOTO_PLACES = ["phố cổ Hà Nội", "Sài Gòn by night", "Hội An", "Đà Nẵng", "Bến Nhà Rồng"]
NETWORK_TOPICS = [
    "Alumni Google, VNG, Shopee chia sẻ", "Startup founder kể chuyện", "PM career path",
    "Chuyển ngành sang IT", "Resume & LinkedIn tips", "Phỏng vấn Big Tech",
]
GAME_TITLES = ["Valorant", "League of Legends", "CS2", "FIFA 26", "TFT"]
LAN_GAMES = ["Age of Empires", "Dota 2", "Overwatch 2", "Rocket League"]
TEACH_SUBJECTS = ["tiếng Anh", "Toán", "Tin học", "tiếng Nhật", "vẽ tranh", "đọc sách"]
CLEAN_PLACES = ["Hồ Tây", "bãi biển Mỹ Khê", "kênh Nhiêu Lộc", "công viên", "khuôn viên trường"]
DONATE_ITEMS = ["sách cho vùng cao", "quần áo mùa đông", "đồ dùng học tập", "máy tính cũ"]
BLOOD_PLACES = ["sân trường", "bệnh viện Bạch Mai", "Chợ Rẫy", "KTX"]
GREEN_PLACES = ["khuôn viên trường", "công viên Cầu Giấy", "bờ sông Sài Gòn", "khu dân cư"]

LANG_SKILLS = [
    "IELTS Speaking Part 2 & 3", "TOEIC Listening", "tiếng Nhật giao tiếp N4",
    "tiếng Hàn sơ cấp", "Presentation in English", "IELTS Writing Task 2",
]

# ── Group name templates ──
GROUP_NAME_TEMPLATES = [
    "{uni_short} {major} K{k}",
    "CLB {club_type} {uni_short}",
    "{topic} Vietnam",
    "Cộng đồng {topic} {city}",
    "{uni_short} {club_type}",
    "Team {topic} {uni_short}",
    "Nhóm học {subject_short}",
    "{city} {club_type} Club",
]

CLUB_TYPES = [
    "Lập trình", "Guitar", "Nhiếp ảnh", "Tiếng Anh", "Tiếng Nhật", "Startup",
    "Bóng rổ", "Cầu lông", "Chạy bộ", "Yoga", "Sách", "Volunteer", "K-pop Dance",
    "Chess", "Debate", "Music", "Film", "Board Game", "Esports", "Robotics",
    "AI Research", "Blockchain", "Marketing", "Trading", "Camping",
    "Cooking", "Writing", "Design", "Gym", "Swimming", "Tennis",
]

TOPIC_NAMES = [
    "React", "Python", "AI/ML", "DevOps", "Mobile Dev", "Data Science",
    "Cybersecurity", "Game Dev", "Web3", "Cloud Computing", "Open Source",
    "Competitive Programming", "UX/UI Design", "Embedded Systems",
    "Fintech", "EdTech", "Digital Marketing", "Product Management",
    "System Design", "Backend Engineering", "Flutter", "Rust", "Go",
]

CITIES = ["Hà Nội", "Sài Gòn", "Đà Nẵng"]
SUBJECT_SHORTS = [
    "Giải tích", "CTDL", "OOP", "Mạng", "CSDL", "HĐH", "AI",
    "XSTK", "Vật lý", "Hoá đại cương", "Kinh tế vi mô", "Tiếng Anh",
]

GROUP_DESC_TEMPLATES = [
    "Nhóm học tập chung cho sinh viên {major}. Chia sẻ tài liệu, giải bài tập, ôn thi.",
    "Cộng đồng {topic} cho sinh viên VN. Chia sẻ kinh nghiệm, code review, mentoring.",
    "CLB {club} - Giao lưu, luyện tập, thi đấu. Welcome mọi trình độ!",
    "Kết nối sinh viên có đam mê {topic}. Meetup hàng tuần, project chung.",
    "Nhóm dành cho ai yêu thích {topic}. Sharing, learning, growing together.",
    "Sinh hoạt hàng tuần. Học hỏi, networking, và vui chơi cùng nhau.",
    "Nơi kết nối những bạn trẻ đam mê {topic}. Không giới hạn trường.",
]

# ── Comment pools ──
ACTIVITY_COMMENTS = [
    "Hay quá, mình đăng ký tham gia nhé!", "Có cần chuẩn bị gì trước không bạn?",
    "Lần trước tham gia rất vui, lần này rủ thêm bạn.", "Mấy giờ chính xác vậy bạn?",
    "Mình chưa có kinh nghiệm, tham gia được không ạ?", "Tuyệt vời! Đúng thứ mình cần 🔥",
    "Ai đi từ KTX không, mình đi chung?", "Bạn share lại tài liệu sau buổi học nhé?",
    "Cảm ơn bạn đã tổ chức! Rất bổ ích 👍", "Cuối tuần được không ạ?",
    "Có online không bạn?", "Gặp mọi người ở đó nhé!", "Có giới hạn số người không?",
    "Mang theo laptop được chứ?", "Trời mưa thì sao bạn?", "Mình 5 người đăng ký chung OK?",
    "Buổi trước rất chất lượng, thanks host.", "Có group chat không?",
    "Năm nhất tham gia được không?", "Miễn phí hay có phí bạn?",
    "Địa điểm cụ thể ở đâu ạ?", "Mình sẽ đến muộn 15p, OK không?",
    "Quá xịn! Share link đăng ký đi 🙌", "Mình lần đầu, mong mọi người chỉ bảo!",
    "Bạn ơi còn slot không?", "Mình đăng ký 2 người nhé!", "Quá hay, share cho bạn bè luôn!",
    "Mình đã đăng ký rồi, hẹn gặp!", "Hoạt động kéo dài bao lâu vậy ạ?",
    "Có cần mặc đồ gì đặc biệt không?", "Bạn có link Google Maps không?",
    "Mình ở Q7, đi có xa không?", "Mong có nhiều buổi như vậy hơn!",
    "Cảm ơn bạn, mình note lịch rồi!", "Lần đầu biết tới nhóm, rất hay!",
    "Ai rủ mình đi với, mình ngại đi một mình 😅", "Chắc chắn tham gia!",
    "Mình share link lên group lớp nhé?", "Cần ID sinh viên không bạn?",
    "Tuyệt vời, cuối cùng cũng có buổi {category} rồi!", "Mình bookmark rồi, thanks!",
]

DOCUMENT_COMMENTS = [
    "Tài liệu rất chi tiết, cảm ơn đã share!", "Có phiên bản mới hơn không?",
    "Tải được rồi, cảm ơn nhiều 🙏", "Slide này của thầy/cô nào?",
    "Có thêm đề thi năm trước không?", "Mình bổ sung thêm phần chương 5 nhé.",
    "File mở bị lỗi font, check lại giúp?", "Quá hữu ích cho kỳ thi! Bookmarked.",
    "Có tóm tắt ngắn gọn hơn không?", "Đang cần tài liệu này, cảm ơn!",
    "Bạn có thể share thêm phần bài tập không?", "Save lại để ôn thi cuối kỳ!",
    "Chất lượng quá, bạn tổng hợp giỏi thật!", "Có version tiếng Anh không ạ?",
    "Mình in ra học được không nhỉ?", "Cảm ơn bạn, đúng lúc mình cần!",
    "Link drive bị hết hạn rồi bạn ơi.", "Update thêm phần mới nhé bạn!",
    "Đề thi này năm nào vậy?", "Mình share cho nhóm lớp nhé, cảm ơn!",
]

REPLY_POOL = [
    "Đồng ý!", "Mình cũng nghĩ vậy 😄", "Cảm ơn bạn feedback!",
    "Mình cập nhật sớm nhé.", "Để mình hỏi host rồi rep sau.", "OK noted!",
    "Thanks nhiều!", "Mình cũng muốn biết luôn.", "Haha đúng rồi!",
    "Bạn có thể inbox mình thêm chi tiết không?", "Mình cũng vậy nè!",
    "Good idea!", "Chuẩn luôn bạn.", "Mình sẽ cập nhật trong group chat nhé.",
    "Noted rồi, cảm ơn bạn!", "Mình cũng đang phân vân điều này.",
]

# ── Document templates ──
DOC_TEMPLATES = [
    ("Slide {subject} - Chương {ch}", "Slide bài giảng chương {ch}: {topic}.",
     "{subj_file}_ch{ch}.pdf", "application/pdf"),
    ("Đề thi cuối kỳ {subject} {year}", "Đề thi + đáp án.",
     "de_thi_{subj_file}_{year}.pdf", "application/pdf"),
    ("Tóm tắt {subject}", "Bản tóm tắt ngắn gọn, dễ hiểu. Có sơ đồ tư duy.",
     "tomtat_{subj_file}.pdf", "application/pdf"),
    ("Hướng dẫn {tech}", "Step-by-step từ cơ bản đến nâng cao. Có hình minh hoạ.",
     "{tech_file}_tutorial.pdf", "application/pdf"),
    ("Cheat Sheet {tech}", "Tổng hợp các hàm/lệnh thường dùng. 2 trang A4.",
     "{tech_file}_cheatsheet.pdf", "application/pdf"),
    ("Báo cáo đồ án: {project_title}", "Báo cáo đồ án kỳ cuối.",
     "report_{proj_file}.pdf", "application/pdf"),
    ("Template CV {field}", "CV template chuẩn ATS.",
     "cv_template_{field_file}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("Kinh nghiệm phỏng vấn {company}", "Chia sẻ chi tiết các vòng phỏng vấn.",
     "interview_{comp_file}.pdf", "application/pdf"),
    ("Bộ flashcard {flashcard_topic}", "Flashcard kèm ví dụ.",
     "flashcard_{fc_file}.pdf", "application/pdf"),
    ("Infographic: {info_topic}", "Infographic trực quan, dễ hiểu.",
     "infographic_{info_file}.png", "image/png"),
]

DOC_SUBJECTS = SUBJECTS
DOC_TECHS = ["Docker", "Git", "Python Pandas", "React Hooks", "FastAPI", "SQL", "Linux CLI",
             "AWS", "Kubernetes", "Redis", "Nginx", "GraphQL", "TypeScript", "Rust basics"]
DOC_PROJECTS = [
    ("Smart Parking System", "smart_parking"), ("E-commerce Platform", "ecommerce"),
    ("Chat Application", "chat_app"), ("Library Management", "library_mgmt"),
    ("Food Delivery App", "food_delivery"), ("Student Portal", "student_portal"),
    ("IoT Weather Station", "iot_weather"), ("Social Media Dashboard", "social_dashboard"),
    ("Budget Tracker", "budget_tracker"), ("Online Exam System", "exam_system"),
    ("Healthcare App", "health_app"), ("Music Streaming", "music_stream"),
]
DOC_COMPANIES = [
    ("FPT Software", "fpt"), ("VNG", "vng"), ("Shopee", "shopee"), ("Grab", "grab"),
    ("Google", "google"), ("Samsung VN", "samsung"), ("Deloitte", "deloitte"),
    ("Tiki", "tiki"), ("MoMo", "momo"), ("Zalo", "zalo"), ("Microsoft", "microsoft"),
]
DOC_FIELDS = [
    ("IT/Software Engineer", "it"), ("Data Analyst", "data"), ("Marketing", "marketing"),
    ("Finance", "finance"), ("Design", "design"), ("PM/BA", "pmba"),
]
DOC_FLASHCARDS = [
    ("Kanji N3", "kanji_n3"), ("IELTS Vocabulary", "ielts_vocab"),
    ("TOEIC 600 words", "toeic_600"), ("Accounting Terms", "accounting"),
    ("Marketing Concepts", "marketing"), ("Legal Terms", "legal"),
]
DOC_INFOGRAPHICS = [
    ("Lộ trình Web Dev", "webdev_roadmap"), ("Data Science Career Path", "ds_career"),
    ("Design Thinking Process", "design_thinking"), ("Agile vs Waterfall", "agile_waterfall"),
    ("Git Workflow", "git_workflow"), ("Cloud Architecture", "cloud_arch"),
]

# ── Notification & Report ──
NOTIF_TEMPLATES = [
    ("join_request", "activity", "{actor} đã gửi yêu cầu tham gia \"{target}\""),
    ("join_approved", "activity", "Yêu cầu tham gia \"{target}\" đã được chấp nhận"),
    ("join_declined", "activity", "Yêu cầu tham gia \"{target}\" đã bị từ chối"),
    ("new_comment", "activity", "{actor} đã bình luận về hoạt động \"{target}\""),
    ("new_comment", "document", "{actor} đã bình luận về tài liệu \"{target}\""),
    ("new_like", "activity", "{actor} đã thích hoạt động \"{target}\""),
    ("new_like", "document", "{actor} đã thích tài liệu \"{target}\""),
    ("new_follower", "user", "{actor} đã bắt đầu theo dõi bạn"),
    ("group_invite", "group", "{actor} đã mời bạn tham gia nhóm \"{target}\""),
    ("activity_reminder", "activity", "Hoạt động \"{target}\" sẽ bắt đầu trong 1 giờ nữa"),
    ("new_document", "document", "{actor} đã chia sẻ tài liệu mới trong nhóm"),
    ("group_join", "group", "{actor} đã tham gia nhóm \"{target}\""),
]

REPORT_REASONS = [
    "Nội dung spam", "Thông tin sai sự thật", "Ngôn ngữ không phù hợp",
    "Quảng cáo trá hình", "Vi phạm bản quyền", "Nội dung lừa đảo",
    "Quấy rối người dùng khác", "Nội dung không liên quan", "Giả mạo danh tính",
    "Nội dung bạo lực", "Spam link ngoài", "Chia sẻ thông tin cá nhân người khác",
]

REPORT_DESCRIPTIONS = [
    "Nội dung này vi phạm quy định cộng đồng.",
    "Người dùng này liên tục đăng nội dung không phù hợp.",
    "Tài liệu này chứa thông tin sai lệch, gây hiểu nhầm.",
    "Hoạt động này có dấu hiệu quảng cáo, không phải hoạt động thật.",
    "Nội dung copy từ nguồn khác mà không ghi nguồn.",
    None, None, None,  # Some without description
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GENERATOR HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_users(count: int) -> list[dict]:
    """Generate `count` unique, realistic Vietnamese user profiles."""
    combos = list(itertools.product(LAST_NAMES, MIDDLE_NAMES, FIRST_NAMES))
    random.shuffle(combos)
    combos = combos[:count]

    users = []
    used_usernames = set()
    for i, (last, middle, first) in enumerate(combos):
        full_name = f"{last} {middle} {first}"
        base_username = f"{first.lower()}.{last.lower()}"
        # Remove Vietnamese diacritics for username
        username = _remove_accents(base_username)
        # Ensure unique
        if username in used_usernames:
            username = f"{username}{i}"
        used_usernames.add(username)

        uni_idx = i % len(UNIVERSITIES)
        uni_name, uni_short = UNIVERSITIES[uni_idx]

        k = random.randint(64, 69)
        year = random.randint(1, 4)
        major = random.choice(MAJORS)
        hobby = random.choice(HOBBIES)
        interest = random.choice(INTERESTS)
        extra = random.choice(EXTRAS)
        doing = random.choice(DOINGS)

        bio_template = random.choice(BIO_TEMPLATES)
        bio = bio_template.format(
            major=major, k=k, uni=uni_name, hobby=hobby,
            interest=interest, extra=extra, year=year,
            role="Sinh viên", doing=doing,
        )

        email = f"{username}@student.{uni_short}.edu.vn"

        users.append({
            "username": username,
            "email": email,
            "full_name": full_name,
            "bio": bio,
            "university": uni_name,
        })

    return users


def _remove_accents(s: str) -> str:
    """Convert Vietnamese characters to ASCII for usernames."""
    accent_map = {
        'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'đ': 'd',
        'Đ': 'D',
    }
    return ''.join(accent_map.get(c, c) for c in s)


def _fill_activity(cat: str, title_t: str, desc_t: str) -> tuple[str, str]:
    """Fill in an activity template with random data."""
    fills = {
        "subject": random.choice(SUBJECTS),
        "detail": f"Chương {random.randint(1,8)}",
        "detail_desc": f"chương {random.randint(1,8)} và bài tập",
        "tech_topic": random.choice(TECH_TOPICS),
        "paper": random.choice(PAPERS),
        "lang_skill": random.choice(LANG_SKILLS),
        "project": random.choice(PROJECTS),
        "interview_type": random.choice(INTERVIEW_TYPES),
        "book": random.choice(BOOKS),
        "distance": random.choice(DISTANCES),
        "place": random.choice(["hồ", "công viên", "sân trường", "bờ sông"]),
        "day": str(random.randint(2, 7)),
        "route": random.choice(ROUTES),
        "pool": random.choice(POOLS),
        "mountain": random.choice(MOUNTAINS),
        "match": random.choice(MATCHES),
        "chat_topic": random.choice(CHAT_TOPICS),
        "social_type": random.choice(SOCIAL_TYPES),
        "movie": random.choice(MOVIES),
        "food_theme": random.choice(FOOD_THEMES),
        "game": random.choice(GAMES_BOARD),
        "month": str(random.randint(1, 12)),
        "network_topic": random.choice(NETWORK_TOPICS),
        "photo_place": random.choice(PHOTO_PLACES),
        "park": random.choice(PARKS),
        "game_title": random.choice(GAME_TITLES),
        "season": str(random.randint(1, 5)),
        "clash": f"mùa {random.randint(1,4)}",
        "num": str(random.randint(1, 10)),
        "lan_game": random.choice(LAN_GAMES),
        "teach_subject": random.choice(TEACH_SUBJECTS),
        "clean_place": random.choice(CLEAN_PLACES),
        "donate_item": random.choice(DONATE_ITEMS),
        "blood_place": random.choice(BLOOD_PLACES),
        "green_place": random.choice(GREEN_PLACES),
        "category": cat,
    }
    title = title_t.format(**fills)
    desc = desc_t.format(**fills)
    return title[:150], desc


def generate_group_name(idx: int) -> tuple[str, str]:
    """Generate a unique group name + description."""
    template = random.choice(GROUP_NAME_TEMPLATES)
    uni_name, uni_short = random.choice(UNIVERSITIES)
    k = random.randint(64, 69)
    major = random.choice(MAJORS)
    club = random.choice(CLUB_TYPES)
    topic = random.choice(TOPIC_NAMES)
    city = random.choice(CITIES)
    subject_short = random.choice(SUBJECT_SHORTS)

    name = template.format(
        uni_short=uni_short.upper(),
        major=major, k=k, club_type=club, topic=topic,
        city=city, subject_short=subject_short,
    )
    # Ensure uniqueness by appending idx if needed
    name = f"{name} #{idx}" if idx > 50 else name
    name = name[:100]

    desc_t = random.choice(GROUP_DESC_TEMPLATES)
    desc = desc_t.format(major=major, topic=topic, club=club)

    return name, desc


def generate_documents(count: int) -> list[dict]:
    """Generate `count` unique documents."""
    docs = []
    for i in range(count):
        template = random.choice(DOC_TEMPLATES)
        title_t, desc_t, fname_t, ftype = template

        subject = random.choice(DOC_SUBJECTS)
        tech = random.choice(DOC_TECHS)
        ch = random.randint(1, 10)
        year = random.randint(2022, 2026)
        proj_name, proj_file = random.choice(DOC_PROJECTS)
        comp_name, comp_file = random.choice(DOC_COMPANIES)
        field_name, field_file = random.choice(DOC_FIELDS)
        fc_name, fc_file = random.choice(DOC_FLASHCARDS)
        info_name, info_file = random.choice(DOC_INFOGRAPHICS)

        subj_file = _remove_accents(subject.lower().replace(" ", "_").replace("-", "_"))
        tech_file = tech.lower().replace(" ", "_").replace("&", "and").replace("/", "_")

        fills = {
            "subject": subject, "ch": ch, "topic": f"phần {ch}",
            "year": year, "tech": tech,
            "subj_file": subj_file, "tech_file": tech_file,
            "project_title": proj_name, "proj_file": proj_file,
            "company": comp_name, "comp_file": comp_file,
            "field": field_name, "field_file": field_file,
            "flashcard_topic": fc_name, "fc_file": fc_file,
            "info_topic": info_name, "info_file": info_file,
        }

        try:
            title = title_t.format(**fills)[:200]
            desc = desc_t.format(**fills)
            fname = fname_t.format(**fills)[:255]
        except KeyError:
            title = f"Tài liệu học tập #{i+1}"
            desc = "Tài liệu hữu ích cho sinh viên."
            fname = f"document_{i+1}.pdf"

        fsize = random.randint(200_000, 10_000_000)

        docs.append({
            "title": title,
            "description": desc,
            "file_name": fname,
            "file_type": ftype,
            "file_size": fsize,
        })

    return docs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN SEED FUNCTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NUM_USERS = 300
NUM_GROUPS = 300
NUM_ACTIVITIES = 350
NUM_FOLLOWS = 800
NUM_DOCUMENTS = 300
NUM_COMMENTS = 350
NUM_REPLIES = 120
NUM_LIKES = 500
NUM_NOTIFICATIONS = 300
NUM_REPORTS = 300
BATCH_SIZE = 100


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=5)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # ── Ensure all tables exist ──
    print("🔧 Ensuring database tables exist...")
    from app.core.models import Base
    # Import all models so Base.metadata knows about them
    import app.modules.users.models       # noqa: F401
    import app.modules.groups.models      # noqa: F401
    import app.modules.activities.models  # noqa: F401
    import app.modules.participation.models  # noqa: F401
    import app.modules.documents.models   # noqa: F401
    import app.modules.interactions.models  # noqa: F401
    import app.modules.notifications.models  # noqa: F401
    import app.modules.reports.models     # noqa: F401

    async with engine.begin() as conn:
        # PostGIS extension required for Geography columns
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)
    print("   ✅ All tables ready")

    async with async_session() as db:
        # ── Clear existing data ──
        print("🗑️  Clearing existing data...")
        # Get list of actual tables in the database
        result = await db.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ))
        existing_tables = {row[0] for row in result.fetchall()}

        tables_to_truncate = [
            "reports", "notifications", "content_likes", "comments",
            "join_requests", "documents", "activities",
            "group_members", "groups", "user_follows", "users",
        ]
        tables_to_truncate = [t for t in tables_to_truncate if t in existing_tables]

        if tables_to_truncate:
            await db.execute(text(
                f"TRUNCATE TABLE {', '.join(tables_to_truncate)} CASCADE"
            ))
        await db.commit()
        print(f"   ✅ Cleared {len(tables_to_truncate)} tables")

        # ═══════════════════════════════════════════════════
        #  1. ADMIN
        # ═══════════════════════════════════════════════════
        print("👤 Creating admin user...")
        admin = User(
            email="admin@uniconnect.vn", username="admin",
            full_name="System Administrator",
            password_hash=hash_password("admin123"),
            role=UserRole.admin,
            bio="Quản trị hệ thống UniConnect.",
            university="UniConnect Team",
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        # ═══════════════════════════════════════════════════
        #  2. USERS (300)
        # ═══════════════════════════════════════════════════
        print(f"👥 Creating {NUM_USERS} student users...")
        user_data_list = generate_users(NUM_USERS)
        users = []
        hashed_pw = hash_password("password123")  # Hash once, reuse

        for i in range(0, len(user_data_list), BATCH_SIZE):
            batch = user_data_list[i:i+BATCH_SIZE]
            for ud in batch:
                user = User(
                    username=ud["username"], email=ud["email"],
                    full_name=ud["full_name"], bio=ud["bio"],
                    university=ud["university"],
                    password_hash=hashed_pw,
                    role=UserRole.student,
                )
                db.add(user)
                users.append(user)
            await db.commit()
            print(f"   ... {min(i+BATCH_SIZE, len(user_data_list))}/{len(user_data_list)}")

        for u in users:
            await db.refresh(u)
        print(f"   ✅ {len(users)} students created")

        # ═══════════════════════════════════════════════════
        #  3. FOLLOWS (800+)
        # ═══════════════════════════════════════════════════
        print(f"🔗 Creating {NUM_FOLLOWS}+ follow relationships...")
        follow_pairs = set()
        follow_count = 0

        for user in users:
            num_follows = random.randint(2, 6)
            targets = random.sample([u for u in users if u.id != user.id],
                                    min(num_follows, len(users) - 1))
            for target in targets:
                pair = (user.id, target.id)
                if pair not in follow_pairs:
                    follow_pairs.add(pair)
                    db.add(UserFollow(follower_id=user.id, following_id=target.id))
                    follow_count += 1

                    if follow_count % BATCH_SIZE == 0:
                        await db.flush()

        await db.commit()
        print(f"   ✅ {follow_count} follows created")

        # ═══════════════════════════════════════════════════
        #  4. GROUPS (300)
        # ═══════════════════════════════════════════════════
        print(f"📁 Creating {NUM_GROUPS} groups...")
        groups = []
        used_group_names = set()

        for i in range(NUM_GROUPS):
            name, desc = generate_group_name(i)
            # Ensure unique name
            while name in used_group_names:
                name = f"{name[:90]}_{i}"
            used_group_names.add(name)

            group = Group(
                name=name, description=desc,
                owner_id=random.choice(users).id,
            )
            db.add(group)
            groups.append(group)

            if (i + 1) % BATCH_SIZE == 0:
                await db.commit()
                print(f"   ... {i+1}/{NUM_GROUPS}")

        await db.commit()
        for g in groups:
            await db.refresh(g)
        print(f"   ✅ {len(groups)} groups created")

        # ═══════════════════════════════════════════════════
        #  5. GROUP MEMBERS (900+)
        # ═══════════════════════════════════════════════════
        print("👥 Adding group members...")
        member_count = 0
        for group in groups:
            # Owner as admin
            db.add(GroupMember(group_id=group.id, user_id=group.owner_id, role=GroupRole.admin))
            member_count += 1

            # 2-6 random members
            num_m = random.randint(2, 6)
            candidates = [u for u in users if u.id != group.owner_id]
            for member_user in random.sample(candidates, min(num_m, len(candidates))):
                db.add(GroupMember(group_id=group.id, user_id=member_user.id, role=GroupRole.member))
                member_count += 1

            if member_count % (BATCH_SIZE * 3) == 0:
                await db.flush()

        await db.commit()
        print(f"   ✅ {member_count} group memberships created")

        # ═══════════════════════════════════════════════════
        #  6. ACTIVITIES (350)
        # ═══════════════════════════════════════════════════
        print(f"📅 Creating {NUM_ACTIVITIES} activities...")
        activities = []
        categories = list(ACTIVITY_TEMPLATES.keys())

        for i in range(NUM_ACTIVITIES):
            cat = random.choice(categories)
            title_t, desc_t = random.choice(ACTIVITY_TEMPLATES[cat])
            title, desc = _fill_activity(cat, title_t, desc_t)

            loc = random.choice(ALL_LOCATIONS)
            lat, lng, loc_name = loc
            # Add small random offset for uniqueness
            lat += random.uniform(-0.005, 0.005)
            lng += random.uniform(-0.005, 0.005)

            host = random.choice(users)
            group_id = random.choice(groups).id if random.random() < 0.35 else None

            day_offset = random.randint(-10, 21)
            hour = random.choice([7, 8, 9, 10, 14, 15, 16, 17, 18, 19, 20])
            start_time = (datetime.datetime.now(datetime.timezone.utc)
                          + datetime.timedelta(days=day_offset, hours=hour - 12))
            duration = random.choice([1, 1.5, 2, 2.5, 3, 4])
            max_p = random.choice([5, 8, 10, 12, 15, 20, 25, 30, 50])
            privacy = ActivityPrivacy.public if random.random() < 0.85 else ActivityPrivacy.private

            act = Activity(
                title=title, description=desc, category=cat,
                location=f"POINT({lng} {lat})",
                location_name=loc_name,
                start_time=start_time,
                end_time=start_time + datetime.timedelta(hours=duration),
                host_id=host.id, group_id=group_id,
                max_participants=max_p, current_participants=1,
                privacy=privacy,
                require_approval=random.random() < 0.6,
            )
            db.add(act)
            activities.append(act)

            if (i + 1) % BATCH_SIZE == 0:
                await db.commit()
                print(f"   ... {i+1}/{NUM_ACTIVITIES}")

        await db.commit()
        for a in activities:
            await db.refresh(a)
        print(f"   ✅ {len(activities)} activities created")

        # ═══════════════════════════════════════════════════
        #  7. JOIN REQUESTS (500+)
        # ═══════════════════════════════════════════════════
        print("📋 Creating join requests...")
        jr_count = 0
        jr_messages = [
            "Mình muốn tham gia!", "Cho mình đăng ký với nhé.",
            "Mình quan tâm, cho mình join nha!", "Rất muốn tham gia ạ!",
            "Mình và 1 bạn nữa muốn đăng ký.", None, None, None,
        ]

        for act in activities:
            # Host approved
            db.add(JoinRequest(
                activity_id=act.id, user_id=act.host_id,
                status=RequestStatus.approved,
            ))
            jr_count += 1

            # 1-3 others
            num_req = random.randint(1, 3)
            candidates = [u for u in users if u.id != act.host_id]
            for user in random.sample(candidates, min(num_req, len(candidates))):
                r = random.random()
                status = (RequestStatus.approved if r < 0.55
                          else RequestStatus.pending if r < 0.80
                          else RequestStatus.declined if r < 0.95
                          else RequestStatus.cancelled)

                jr = JoinRequest(
                    activity_id=act.id, user_id=user.id,
                    status=status, message=random.choice(jr_messages),
                )
                if status in (RequestStatus.approved, RequestStatus.declined):
                    jr.responded_at = (datetime.datetime.now(datetime.timezone.utc)
                                       - datetime.timedelta(hours=random.randint(1, 72)))
                db.add(jr)
                jr_count += 1

            if jr_count % (BATCH_SIZE * 2) == 0:
                await db.flush()

        await db.commit()
        print(f"   ✅ {jr_count} join requests created")

        # ═══════════════════════════════════════════════════
        #  8. DOCUMENTS (300)
        # ═══════════════════════════════════════════════════
        print(f"📄 Creating {NUM_DOCUMENTS} documents...")
        doc_data_list = generate_documents(NUM_DOCUMENTS)
        docs = []

        for i, dd in enumerate(doc_data_list):
            if dd["file_type"] == "application/pdf":
                file_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
            elif dd["file_type"] == "image/png":
                file_url = "https://picsum.photos/800/600"
            elif "wordprocessingml" in dd["file_type"]:
                file_url = "https://calibre-ebook.com/downloads/demos/demo.docx"
            else:
                file_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

            doc = Document(
                title=dd["title"], description=dd["description"],
                file_name=dd["file_name"], file_type=dd["file_type"],
                file_size=dd["file_size"],
                file_url=file_url,
                author_id=random.choice(users).id,
                group_id=random.choice(groups).id if random.random() < 0.45 else None,
            )
            db.add(doc)
            docs.append(doc)

            if (i + 1) % BATCH_SIZE == 0:
                await db.commit()
                print(f"   ... {i+1}/{NUM_DOCUMENTS}")

        await db.commit()
        for d in docs:
            await db.refresh(d)
        print(f"   ✅ {len(docs)} documents created")

        # ═══════════════════════════════════════════════════
        #  9. COMMENTS (350) + REPLIES (120)
        # ═══════════════════════════════════════════════════
        print(f"💬 Creating {NUM_COMMENTS} comments + {NUM_REPLIES} replies...")
        comment_objs = []

        # Comments on activities
        act_comment_count = int(NUM_COMMENTS * 0.7)
        for _ in range(act_comment_count):
            act = random.choice(activities)
            comment = Comment(
                target_type="activity", target_id=act.id,
                user_id=random.choice(users).id,
                content=random.choice(ACTIVITY_COMMENTS),
            )
            db.add(comment)
            comment_objs.append(comment)

        # Comments on documents
        doc_comment_count = NUM_COMMENTS - act_comment_count
        for _ in range(doc_comment_count):
            doc = random.choice(docs)
            comment = Comment(
                target_type="document", target_id=doc.id,
                user_id=random.choice(users).id,
                content=random.choice(DOCUMENT_COMMENTS),
            )
            db.add(comment)
            comment_objs.append(comment)

        await db.commit()
        for c in comment_objs:
            await db.refresh(c)

        # Replies
        reply_count = 0
        for _ in range(NUM_REPLIES):
            parent = random.choice(comment_objs)
            reply = Comment(
                target_type=parent.target_type, target_id=parent.target_id,
                user_id=random.choice(users).id,
                parent_id=parent.id,
                content=random.choice(REPLY_POOL),
            )
            db.add(reply)
            reply_count += 1

        await db.commit()
        print(f"   ✅ {len(comment_objs)} comments + {reply_count} replies created")

        # ═══════════════════════════════════════════════════
        #  10. CONTENT LIKES (500+)
        # ═══════════════════════════════════════════════════
        print(f"❤️  Creating {NUM_LIKES}+ likes...")
        like_pairs = set()
        like_count = 0

        # Likes on activities (~50%)
        for _ in range(int(NUM_LIKES * 0.5)):
            act = random.choice(activities)
            liker = random.choice(users)
            pair = ("activity", act.id, liker.id)
            if pair not in like_pairs:
                like_pairs.add(pair)
                db.add(ContentLike(target_type="activity", target_id=act.id, user_id=liker.id))
                like_count += 1

        # Likes on documents (~30%)
        for _ in range(int(NUM_LIKES * 0.3)):
            doc = random.choice(docs)
            liker = random.choice(users)
            pair = ("document", doc.id, liker.id)
            if pair not in like_pairs:
                like_pairs.add(pair)
                db.add(ContentLike(target_type="document", target_id=doc.id, user_id=liker.id))
                like_count += 1

        # Likes on comments (~20%)
        for _ in range(int(NUM_LIKES * 0.2)):
            comment = random.choice(comment_objs)
            liker = random.choice(users)
            pair = ("comment", comment.id, liker.id)
            if pair not in like_pairs:
                like_pairs.add(pair)
                db.add(ContentLike(target_type="comment", target_id=comment.id, user_id=liker.id))
                like_count += 1

        await db.commit()
        print(f"   ✅ {like_count} likes created")

        # ═══════════════════════════════════════════════════
        #  11. NOTIFICATIONS (300)
        # ═══════════════════════════════════════════════════
        print(f"🔔 Creating {NUM_NOTIFICATIONS} notifications...")
        notif_count = 0

        for i in range(NUM_NOTIFICATIONS):
            n_type, target_type_str, msg_template = random.choice(NOTIF_TEMPLATES)
            recipient = random.choice(users)
            actor = random.choice([u for u in users if u.id != recipient.id])

            if target_type_str == "activity":
                target = random.choice(activities)
                target_name = target.title
            elif target_type_str == "document":
                target = random.choice(docs)
                target_name = target.title
            elif target_type_str == "group":
                target = random.choice(groups)
                target_name = target.name
            else:
                target = recipient
                target_name = actor.full_name or actor.username

            message = msg_template.format(
                actor=actor.full_name or actor.username,
                target=target_name,
            )

            db.add(Notification(
                user_id=recipient.id, actor_id=actor.id,
                type=n_type, target_type=target_type_str,
                target_id=target.id, message=message,
                is_read=random.random() < 0.35,
            ))
            notif_count += 1

            if (i + 1) % BATCH_SIZE == 0:
                await db.flush()

        await db.commit()
        print(f"   ✅ {notif_count} notifications created")

        # ═══════════════════════════════════════════════════
        #  12. REPORTS (300)
        # ═══════════════════════════════════════════════════
        print(f"🚩 Creating {NUM_REPORTS} reports...")
        report_count = 0

        target_pools = (
            [("activity", a.id) for a in activities]
            + [("document", d.id) for d in docs]
            + [("user", u.id) for u in users]
        )

        for i in range(NUM_REPORTS):
            target_type_str, target_id = random.choice(target_pools)
            reporter = random.choice(users)
            status = random.choices(
                ["pending", "resolved", "dismissed"],
                weights=[0.5, 0.3, 0.2],
            )[0]

            db.add(Report(
                reporter_id=reporter.id,
                target_type=target_type_str,
                target_id=target_id,
                reason=random.choice(REPORT_REASONS),
                description=random.choice(REPORT_DESCRIPTIONS),
                status=status,
                admin_note="Đã xem xét và xử lý." if status == "resolved" else None,
                resolved_by=admin.id if status == "resolved" else None,
            ))
            report_count += 1

            if (i + 1) % BATCH_SIZE == 0:
                await db.flush()

        await db.commit()
        print(f"   ✅ {report_count} reports created")

    await engine.dispose()

    # ── Final Summary ──
    print("\n" + "=" * 60)
    print("🎉 SEED COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"""
📊 Summary:
   • 1 admin (admin@uniconnect.vn / admin123)
   • {len(users)} students (password: password123)
   • {follow_count} follow relationships
   • {len(groups)} groups with {member_count} memberships
   • {len(activities)} activities (Hanoi, HCMC, Da Nang)
   • {jr_count} join requests
   • {len(docs)} documents
   • {len(comment_objs)} comments + {reply_count} replies
   • {like_count} content likes
   • {notif_count} notifications
   • {report_count} reports

🔑 Login credentials:
   Admin:   admin@uniconnect.vn / admin123
   Student: <username>@student.<uni>.edu.vn / password123
""")


if __name__ == "__main__":
    asyncio.run(seed())
