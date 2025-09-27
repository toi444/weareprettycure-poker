import streamlit as st
import pandas as pd
import datetime
import os
from datetime import timedelta, time
import time as tm
import zipfile

# Plotlyのインポート（エラー処理付き）
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ページ設定
st.set_page_config(
    page_title="We Are Pretty Cure!",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main-header {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        margin-bottom: 30px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 30px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    .small-metric {
        background: rgba(255, 255, 255, 0.9);
        padding: 8px;
        border-radius: 8px;
        font-size: 12px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# データファイルパス
GAME_DATA_FILE = "poker_games.csv"
BANK_LOANS_FILE = "pbank_loans.csv"
BANK_APPLICATIONS_FILE = "pbank_applications.csv"
BANK_TRANSACTIONS_FILE = "pbank_transactions.csv"
JACKPOT_DATA_FILE = "jackpot_data.csv"
JACKPOT_WINNERS_FILE = "jackpot_winners.csv"
USERS_DATA_FILE = "users_data.csv"
NOTIFICATIONS_FILE = "notifications.csv"

# 初期ユーザーデータ
DEFAULT_USERS = [
    {"username": "admin", "password": "admin123", "role": "admin", "active": True},
    {"username": "player1", "password": "pass1", "role": "player", "active": True},
    {"username": "player2", "password": "pass2", "role": "player", "active": True},
    {"username": "player3", "password": "pass3", "role": "player", "active": True},
    {"username": "player4", "password": "pass4", "role": "player", "active": True},
    {"username": "player5", "password": "pass5", "role": "player", "active": True},
    {"username": "player6", "password": "pass6", "role": "player", "active": True},
    {"username": "player7", "password": "pass7", "role": "player", "active": True},
    {"username": "player8", "password": "pass8", "role": "player", "active": True}
]

def load_users():
    """ユーザーデータを読み込み"""
    if os.path.exists(USERS_DATA_FILE):
        df = pd.read_csv(USERS_DATA_FILE)
        df['active'] = df['active'].astype(bool)
        return df
    else:
        df = pd.DataFrame(DEFAULT_USERS)
        df.to_csv(USERS_DATA_FILE, index=False)
        return df

def save_users(df):
    """ユーザーデータを保存"""
    df.to_csv(USERS_DATA_FILE, index=False)

def add_notification(user, message, type="info"):
    """通知を追加"""
    if os.path.exists(NOTIFICATIONS_FILE):
        df = pd.read_csv(NOTIFICATIONS_FILE)
    else:
        df = pd.DataFrame(columns=['datetime', 'user', 'message', 'type', 'read'])
    
    new_notification = pd.DataFrame([{
        'datetime': pd.Timestamp.now(),
        'user': user,
        'message': message,
        'type': type,
        'read': False
    }])
    
    df = pd.concat([df, new_notification], ignore_index=True)
    df.to_csv(NOTIFICATIONS_FILE, index=False)

def get_notifications(user):
    """未読通知を取得"""
    if os.path.exists(NOTIFICATIONS_FILE):
        df = pd.read_csv(NOTIFICATIONS_FILE)
        return df[(df['user'] == user) & (df['read'] == False)]
    return pd.DataFrame()

def mark_notifications_read(user):
    """通知を既読にする"""
    if os.path.exists(NOTIFICATIONS_FILE):
        df = pd.read_csv(NOTIFICATIONS_FILE)
        df.loc[df['user'] == user, 'read'] = True
        df.to_csv(NOTIFICATIONS_FILE, index=False)

def calculate_play_time(start_time, end_time):
    """プレイ時間を計算（日跨ぎ対応）"""
    start_hours = start_time.hour + start_time.minute / 60
    end_hours = end_time.hour + end_time.minute / 60
    
    if end_time < start_time:
        play_hours = (24 - start_hours) + end_hours
    else:
        play_hours = end_hours - start_hours
    
    return round(play_hours, 1)

def apply_monthly_interest():
    """毎月1日に利息を適用（一律10%）"""
    today = datetime.date.today()
    
    if today.day == 1:
        if os.path.exists(BANK_LOANS_FILE):
            loans_df = pd.read_csv(BANK_LOANS_FILE)
            active_loans = loans_df[loans_df['status'] == 'active']
            
            if not active_loans.empty:
                interest_records = []
                
                for idx in active_loans.index:
                    loan_id = loans_df.loc[idx, 'loan_id']
                    lender = loans_df.loc[idx, 'lender']
                    borrower = loans_df.loc[idx, 'borrower']
                    current_remaining = float(loans_df.loc[idx, 'remaining'])
                    
                    interest = current_remaining * 0.1
                    new_remaining = current_remaining + interest
                    
                    loans_df.loc[idx, 'remaining'] = new_remaining
                    loans_df.loc[idx, 'last_interest_date'] = today
                    
                    interest_record = {
                        'transaction_id': f"INT_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}_{loan_id}",
                        'datetime': pd.Timestamp.now(),
                        'type': 'interest',
                        'from_user': borrower,
                        'to_user': lender,
                        'amount': interest,
                        'loan_id': loan_id,
                        'balance_after': new_remaining,
                        'notes': f'月次利息10% (元残高: {current_remaining:.0f} P)'
                    }
                    interest_records.append(interest_record)
                    
                    add_notification(lender, 
                        f"💰 {borrower}さんからの融資に利息{interest:.0f} Pが追加されました（残高: {new_remaining:.0f} P）", 
                        "success")
                    add_notification(borrower, 
                        f"📈 {lender}さんへの借入に利息{interest:.0f} Pが追加されました（残高: {new_remaining:.0f} P）", 
                        "warning")
                
                loans_df.to_csv(BANK_LOANS_FILE, index=False)
                
                if interest_records:
                    if os.path.exists(BANK_TRANSACTIONS_FILE):
                        trans_df = pd.read_csv(BANK_TRANSACTIONS_FILE)
                        new_trans_df = pd.DataFrame(interest_records)
                        trans_df = pd.concat([trans_df, new_trans_df], ignore_index=True)
                    else:
                        trans_df = pd.DataFrame(interest_records)
                    trans_df.to_csv(BANK_TRANSACTIONS_FILE, index=False)

def init_data():
    """データファイルの初期化"""
    try:
        if not os.path.exists(GAME_DATA_FILE):
            df = pd.DataFrame(columns=['datetime', 'player', 'date', 'start_time', 'end_time', 'play_hours', 'buyin', 'result'])
            df.to_csv(GAME_DATA_FILE, index=False)
        
        if not os.path.exists(BANK_LOANS_FILE):
            df = pd.DataFrame(columns=['loan_id', 'datetime', 'lender', 'borrower', 'amount', 'remaining', 'status', 'due_date', 'last_interest_date'])
            df.to_csv(BANK_LOANS_FILE, index=False)
        
        if not os.path.exists(BANK_APPLICATIONS_FILE):
            df = pd.DataFrame(columns=['app_id', 'datetime', 'type', 'from_user', 'to_user', 'amount', 'loan_id', 'status', 'expire_date', 'message'])
            df.to_csv(BANK_APPLICATIONS_FILE, index=False)
        
        if not os.path.exists(BANK_TRANSACTIONS_FILE):
            df = pd.DataFrame(columns=['transaction_id', 'datetime', 'type', 'from_user', 'to_user', 'amount', 'loan_id', 'balance_after', 'notes'])
            df.to_csv(BANK_TRANSACTIONS_FILE, index=False)
        
        if not os.path.exists(JACKPOT_DATA_FILE):
            df = pd.DataFrame([{'datetime': pd.Timestamp.now(), 'type': 'init', 'amount': 0, 'total': 0, 'admin': 'system', 'notes': '初期化'}])
            df.to_csv(JACKPOT_DATA_FILE, index=False)
        
        if not os.path.exists(JACKPOT_WINNERS_FILE):
            df = pd.DataFrame(columns=['datetime', 'date', 'player', 'hand_type', 'hand_cards', 'table_cards', 'amount', 'paid'])
            df.to_csv(JACKPOT_WINNERS_FILE, index=False)
        
        if not os.path.exists(NOTIFICATIONS_FILE):
            df = pd.DataFrame(columns=['datetime', 'user', 'message', 'type', 'read'])
            df.to_csv(NOTIFICATIONS_FILE, index=False)
            
    except Exception as e:
        st.error(f"データ初期化エラー: {str(e)}")

def init_session_state():
    """セッション状態の初期化"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'page' not in st.session_state:
        st.session_state.page = 'game_report'
    if 'game_registered' not in st.session_state:
        st.session_state.game_registered = False
    if 'loan_applied' not in st.session_state:
        st.session_state.loan_applied = False
    if 'role' not in st.session_state:
        st.session_state.role = None

def get_current_jackpot():
    """現在のジャックポット金額を取得"""
    try:
        df = pd.read_csv(JACKPOT_DATA_FILE)
        if not df.empty:
            return df.iloc[-1]['total']
    except:
        pass
    return 0

def get_latest_jackpot_winner():
    """最新のジャックポット取得者を取得"""
    try:
        if os.path.exists(JACKPOT_WINNERS_FILE):
            df = pd.read_csv(JACKPOT_WINNERS_FILE)
            if not df.empty:
                return df.iloc[-1]
    except:
        pass
    return None

def login_page():
    """ログイン画面"""
    st.markdown("""
        <div class="main-header">
            <h1 style="color: white; font-size: 48px; margin: 0;">🃏 We Are Pretty Cure! 🃏</h1>
            <p style="color: rgba(255, 255, 255, 0.8); font-size: 20px;">Poker Management System</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown("### 🔐 ログイン")
            
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("ユーザー名", placeholder="ユーザー名を入力")
                password = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
                
                if st.form_submit_button("ログイン", use_container_width=True):
                    users_df = load_users()
                    user = users_df[(users_df['username'] == username) & (users_df['password'] == password) & (users_df['active'] == True)]
                    
                    if not user.empty:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = user.iloc[0]['role']
                        st.success("✨ ログイン成功！")
                        st.rerun()
                    else:
                        st.error("❌ ユーザー名またはパスワードが正しくありません")

def game_report_page():
    """ゲームレポートページ"""
    st.markdown("## 🎮 ゲームレポート")
    
    # 登録成功後のリセット処理
    if st.session_state.get('game_registered', False):
        st.session_state.game_registered = False
    
    notifications = get_notifications(st.session_state.username)
    if not notifications.empty:
        st.markdown("### 📬 通知")
        for _, notif in notifications.iterrows():
            if notif['type'] == 'success':
                st.success(notif['message'])
            elif notif['type'] == 'warning':
                st.warning(notif['message'])
            else:
                st.info(notif['message'])
        mark_notifications_read(st.session_state.username)
        st.markdown("---")
    
    st.markdown("### 今日のゲーム結果を入力")
    
    date = st.date_input("📅 日付", value=datetime.date.today())
    
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("🎯 プレイ開始時間", value=time(20, 0))
    with col2:
        end_time = st.time_input("🏁 プレイ終了時間", value=time(23, 0))
    
    play_hours = calculate_play_time(start_time, end_time)
    st.info(f"⏱️ プレイ時間: {play_hours} 時間")
    
    col1, col2 = st.columns(2)
    with col1:
        buyin = st.number_input("💵 バイイン (P)", min_value=0, step=1000, value=0)
    with col2:
        result = st.number_input("📊 収支 (P)", step=1000, value=0)
    
    # チェックボックスをユニークなキーで管理
    confirm_key = "game_confirm"
    confirm = st.checkbox("⚠️ 上記の内容で登録することを確認しました", key=confirm_key)
    
    if st.button("📊 登録する", use_container_width=True, disabled=not confirm):
        try:
            df = pd.read_csv(GAME_DATA_FILE) if os.path.exists(GAME_DATA_FILE) else pd.DataFrame()
            new_data = pd.DataFrame([{
                'datetime': pd.Timestamp.now(),
                'player': st.session_state.username,
                'date': date,
                'start_time': start_time.strftime('%H:%M'),
                'end_time': end_time.strftime('%H:%M'),
                'play_hours': play_hours,
                'buyin': buyin,
                'result': result
            }])
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(GAME_DATA_FILE, index=False)
            
            st.balloons()
            st.success("✨ ゲーム結果を登録しました！")
            
            if result > 0:
                st.success(f"🎉 本日の利益: +{result:,} P")
            elif result < 0:
                st.error(f"😢 本日の損失: {result:,} P")
            else:
                st.info("😐 本日はプラマイゼロでした")
            
            # チェックボックスをリセット
            if confirm_key in st.session_state:
                del st.session_state[confirm_key]
            
            st.session_state.game_registered = True
            tm.sleep(1)
            st.rerun()
                
        except Exception as e:
            st.error(f"登録エラー: {str(e)}")
    
    st.markdown("---")
    st.markdown("### 📊 最近の履歴（最新3件）")
    
    try:
        if os.path.exists(GAME_DATA_FILE):
            df = pd.read_csv(GAME_DATA_FILE)
            user_df = df[df['player'] == st.session_state.username].copy()
            
            if not user_df.empty:
                user_df = user_df.sort_values('datetime', ascending=False).head(3).reset_index(drop=True)
                
                for idx, row in user_df.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{row['date']}** ({row['start_time']} - {row['end_time']})")
                        result_emoji = "🎉" if row['result'] > 0 else "😢" if row['result'] < 0 else "😐"
                        st.write(f"{result_emoji} 収支: {row['result']:,} P (バイイン: {row['buyin']:,} P)")
                        st.write(f"⏱️ プレイ時間: {row['play_hours']}時間")
                    
                    with col2:
                        if row['result'] >= 10000:
                            st.success("大勝ち！")
                        elif row['result'] <= -10000:
                            st.error("大負け！")
                    
                    with col3:
                        actual_idx = df[df['player'] == st.session_state.username].sort_values('datetime', ascending=False).head(3).index[idx]
                        if st.button("🗑️ 削除", key=f"del_game_{actual_idx}"):
                            df = pd.read_csv(GAME_DATA_FILE)
                            df = df.drop(actual_idx).reset_index(drop=True)
                            df.to_csv(GAME_DATA_FILE, index=False)
                            st.success("記録を削除しました")
                            st.rerun()
                    
                    st.markdown("---")
            else:
                st.info("📝 まだゲーム履歴がありません")
        else:
            st.info("📝 まだゲーム履歴がありません")
    except Exception as e:
        st.info("📝 まだゲーム履歴がありません")

def pbank_page():
    """P-BANK ページ（完全統合版）"""
    st.markdown("## 💰 P-BANK")
    
    # 利息の自動適用（毎月1日）
    apply_monthly_interest()
    
    # 融資申請後のリセット処理
    if st.session_state.get('loan_applied', False):
        st.session_state.loan_applied = False
    
    total_lent = 0
    total_borrowed = 0
    pending_apps = 0
    interest_earned = 0  # 受取利息累計
    interest_paid = 0    # 支払利息累計
    
    try:
        if os.path.exists(BANK_LOANS_FILE):
            loans_df = pd.read_csv(BANK_LOANS_FILE)
            loans_df['amount'] = pd.to_numeric(loans_df['amount'], errors='coerce').fillna(0)
            loans_df['remaining'] = pd.to_numeric(loans_df['remaining'], errors='coerce').fillna(0)
            
            my_loans_as_lender = loans_df[(loans_df['lender'] == st.session_state.username) & (loans_df['status'] == 'active')]
            total_lent = my_loans_as_lender['remaining'].sum() if not my_loans_as_lender.empty else 0
            
            my_loans_as_borrower = loans_df[(loans_df['borrower'] == st.session_state.username) & (loans_df['status'] == 'active')]
            total_borrowed = my_loans_as_borrower['remaining'].sum() if not my_loans_as_borrower.empty else 0
        else:
            loans_df = pd.DataFrame()
        
        # 利息履歴から累計を計算
        if os.path.exists(BANK_TRANSACTIONS_FILE):
            trans_df = pd.read_csv(BANK_TRANSACTIONS_FILE)
            # 受取利息（自分が貸し手の利息）
            earned = trans_df[(trans_df['to_user'] == st.session_state.username) & (trans_df['type'] == 'interest')]
            if not earned.empty:
                interest_earned = earned['amount'].sum()
            
            # 支払利息（自分が借り手の利息）
            paid = trans_df[(trans_df['from_user'] == st.session_state.username) & (trans_df['type'] == 'interest')]
            if not paid.empty:
                interest_paid = paid['amount'].sum()
        
        if os.path.exists(BANK_APPLICATIONS_FILE):
            apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
            pending_apps = len(apps_df[(apps_df['to_user'] == st.session_state.username) & (apps_df['status'] == '申込中')])
        else:
            apps_df = pd.DataFrame()
            
    except Exception as e:
        loans_df = pd.DataFrame()
        apps_df = pd.DataFrame()
    
    # 操作方法・ルール説明
    with st.expander("📖 P-BANKの使い方とルール"):
        st.markdown("""
        ### 🏦 P-BANKシステムについて
        
        **基本ルール:**
        - 💰 プレイヤー間でポイント(P)の貸し借りができます
        - 📈 毎月1日に残高の10%が利息として自動加算されます
        - ⏰ 返済期限はありません（いつでも返済可能）
        - ✅ 融資・返済には相手の承認が必要です
        
        **操作方法:**
        1. **融資を受けたい場合** → 「融資申込」タブから申請
        2. **融資を承認する場合** → 「承認待ち」タブで承認/却下
        3. **返済する場合** → 「返済」タブから返済申請
        4. **利息の確認** → 「利息一覧」タブで履歴確認
        
        **利息計算例:**
        - 10,000P借入 → 毎月1日に1,000P（10%）の利息が加算
        - 同時に10,000P貸出がある場合 → 差し引き0P（プラスマイナスゼロ）
        """)
    
    # メイン統計表示
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.success(f"### 💸 貸出額\n## {int(total_lent):,} P")
    with col2:
        st.error(f"### 💳 借入額\n## {int(total_borrowed):,} P")
    with col3:
        net_interest = interest_earned - interest_paid
        color = "success" if net_interest >= 0 else "error"
        getattr(st, color)(f"### 📊 利息収支\n## {int(net_interest):,} P")
    with col4:
        if pending_apps > 0:
            st.warning(f"### 📬 承認待ち\n## {pending_apps} 件")
        else:
            st.info(f"### 📬 承認待ち\n## 0 件")
    
    tabs = st.tabs(["💸 融資申込", "💰 返済", "📋 貸出一覧", "✅ 承認待ち", "📈 利息一覧", "📊 履歴"])
    
    # 融資申込タブ
    with tabs[0]:
        st.markdown("### 💸 新規融資申込")
        st.info("📌 利息: 毎月1日に残高の10%が加算されます | 返済期限: 申込先による ")
        
        users_df = load_users()
        active_users = users_df[(users_df['username'] != st.session_state.username) & (users_df['active'] == True)]['username'].tolist()
        
        if active_users:
            lender = st.selectbox("融資元を選択", active_users)
            amount = st.number_input("申込金額 (P)", min_value=100, step=1000, value=1000)
            message = st.text_area("メッセージ (任意)", placeholder="融資の目的など...")
            
            loan_confirm_key = "loan_confirm"
            confirm = st.checkbox("上記の内容で申込することを確認しました", key=loan_confirm_key)
            
            if st.button("📤 申込する", use_container_width=True, disabled=not confirm):
                try:
                    app_id = f"APP_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}_{st.session_state.username}"
                    
                    new_app = pd.DataFrame([{
                        'app_id': app_id,
                        'datetime': pd.Timestamp.now(),
                        'type': 'loan',
                        'from_user': st.session_state.username,
                        'to_user': lender,
                        'amount': amount,
                        'loan_id': '',
                        'status': '申込中',
                        'expire_date': pd.Timestamp.now() + pd.Timedelta(hours=24),
                        'message': message
                    }])
                    
                    if os.path.exists(BANK_APPLICATIONS_FILE):
                        apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
                        apps_df = pd.concat([apps_df, new_app], ignore_index=True)
                    else:
                        apps_df = new_app
                    
                    apps_df.to_csv(BANK_APPLICATIONS_FILE, index=False)
                    
                    add_notification(lender, f"💰 {st.session_state.username}さんから{amount:,} Pの融資申込がありました", "warning")
                    
                    st.balloons()
                    st.success(f"✅ {lender}さんに{amount:,} Pの融資申込を送信しました！")
                    st.info("相手の承認をお待ちください。")
                    
                    if loan_confirm_key in st.session_state:
                        del st.session_state[loan_confirm_key]
                    
                    st.session_state.loan_applied = True
                    tm.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"申込エラー: {str(e)}")
        else:
            st.info("他のアクティブユーザーがいません")
    
    # 返済タブ（強化版）
    with tabs[1]:
        st.markdown("### 💰 返済")
        
        if not loans_df.empty:
            my_debts = loans_df[(loans_df['borrower'] == st.session_state.username) & (loans_df['status'] == 'active')]
            
            if not my_debts.empty:
                for loan_idx, loan in my_debts.iterrows():
                    with st.expander(f"💳 {loan['lender']}さんへの借入 - {int(loan['remaining']):,} P", expanded=True):
                        st.write(f"借入日: {loan['datetime']}")
                        st.write(f"元本: {int(loan['amount']):,} P")
                        st.write(f"現在残高: {int(loan['remaining']):,} P")
                        
                        # 利息込み金額の計算
                        interest_amount = int(loan['remaining']) - int(loan['amount'])
                        if interest_amount > 0:
                            st.info(f"💹 これまでの利息合計: {interest_amount:,} P")
                        
                        st.markdown("---")
                        
                        # 返済フォーム
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            repay_amount = st.number_input(
                                "返済額 (P)",
                                min_value=100,
                                max_value=int(loan['remaining']),
                                step=1000,
                                value=min(1000, int(loan['remaining'])),
                                key=f"repay_{loan['loan_id']}"
                            )
                        
                        # チェックボックスで確認
                        repay_confirm_key = f"repay_confirm_{loan['loan_id']}"
                        confirm_repay = st.checkbox(
                            f"{repay_amount:,} Pを返済することを確認しました", 
                            key=repay_confirm_key
                        )
                        
                        if st.button(
                            f"💰 {repay_amount:,} P返済申請する", 
                            key=f"repay_btn_{loan['loan_id']}",
                            disabled=not confirm_repay,
                            use_container_width=True
                        ):
                            try:
                                app_id = f"REP_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}_{st.session_state.username}"
                                
                                new_app = pd.DataFrame([{
                                    'app_id': app_id,
                                    'datetime': pd.Timestamp.now(),
                                    'type': 'repayment',
                                    'from_user': st.session_state.username,
                                    'to_user': loan['lender'],
                                    'amount': repay_amount,
                                    'loan_id': loan['loan_id'],
                                    'status': '申込中',
                                    'expire_date': pd.Timestamp.now() + pd.Timedelta(hours=24),
                                    'message': f"返済 ({int(loan['remaining']):,} P中 {repay_amount:,} P)"
                                }])
                                
                                if os.path.exists(BANK_APPLICATIONS_FILE):
                                    apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
                                    apps_df = pd.concat([apps_df, new_app], ignore_index=True)
                                else:
                                    apps_df = new_app
                                
                                apps_df.to_csv(BANK_APPLICATIONS_FILE, index=False)
                                
                                add_notification(loan['lender'], 
                                    f"💰 {st.session_state.username}さんから{repay_amount:,} Pの返済申請がありました", 
                                    "success")
                                
                                st.success(f"✅ {repay_amount:,} Pの返済申請を送信しました")
                                st.info(f"📧 {loan['lender']}さんの承認をお待ちください")
                                
                                # チェックボックスをリセット
                                if repay_confirm_key in st.session_state:
                                    del st.session_state[repay_confirm_key]
                                
                                tm.sleep(1)
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"返済エラー: {str(e)}")
                        
                        # この借入に関する返済履歴を表示
                        st.markdown("#### 📜 この借入の返済履歴")
                        
                        # 返済申請履歴を取得
                        if os.path.exists(BANK_APPLICATIONS_FILE):
                            apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
                            repay_history = apps_df[
                                (apps_df['loan_id'] == loan['loan_id']) & 
                                (apps_df['type'] == 'repayment')
                            ].sort_values('datetime', ascending=False)
                            
                            if not repay_history.empty:
                                for _, repay in repay_history.iterrows():
                                    status_icon = "✅" if repay['status'] == '承認済' else "⏳" if repay['status'] == '申込中' else "❌"
                                    
                                    # 返済履歴の表示
                                    col1, col2, col3 = st.columns([2, 1, 1])
                                    with col1:
                                        st.write(f"{status_icon} {repay['datetime'][:16]}")
                                    with col2:
                                        st.write(f"{int(repay['amount']):,} P")
                                    with col3:
                                        if repay['status'] == '承認済':
                                            st.success("承認済")
                                        elif repay['status'] == '申込中':
                                            st.warning("承認待ち")
                                        else:
                                            st.error("却下")
                                
                                # 承認済みの返済合計
                                approved_repayments = repay_history[repay_history['status'] == '承認済']
                                if not approved_repayments.empty:
                                    total_repaid = approved_repayments['amount'].sum()
                                    st.success(f"📊 承認済み返済合計: {int(total_repaid):,} P")
                                
                                # 申請中の返済
                                pending_repayments = repay_history[repay_history['status'] == '申込中']
                                if not pending_repayments.empty:
                                    pending_total = pending_repayments['amount'].sum()
                                    st.warning(f"⏳ 承認待ち返済: {int(pending_total):,} P")
                            else:
                                st.info("まだ返済履歴はありません")
                        else:
                            st.info("まだ返済履歴はありません")
                        
                        st.markdown("---")
            else:
                st.success("🎉 現在借入はありません")
        else:
            st.success("🎉 現在借入はありません")
    
    # 貸出一覧タブ
    with tabs[2]:
        st.markdown("### 📋 貸出一覧")
        
        if not loans_df.empty:
            my_lendings = loans_df[(loans_df['lender'] == st.session_state.username) & (loans_df['status'] == 'active')]
            
            if not my_lendings.empty:
                for _, loan in my_lendings.iterrows():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{loan['borrower']}さん**")
                        st.write(f"貸付日: {loan['datetime']}")
                        st.write(f"元本: {int(loan['amount']):,} P")
                        st.write(f"現在残高: {int(loan['remaining']):,} P")
                        
                        interest_amount = int(loan['remaining']) - int(loan['amount'])
                        if interest_amount > 0:
                            st.success(f"💹 利息収入合計: {interest_amount:,} P")
                    
                    st.markdown("---")
            else:
                st.info("📝 貸出中の融資はありません")
        else:
            st.info("📝 貸出中の融資はありません")
    
    # 承認待ちタブ
    with tabs[3]:
        st.markdown("### ✅ 承認待ち申請")
        
        if not apps_df.empty:
            my_pending = apps_df[(apps_df['to_user'] == st.session_state.username) & (apps_df['status'] == '申込中')]
            
            if not my_pending.empty:
                for _, app in my_pending.iterrows():
                    with st.expander(f"📬 {app['from_user']}さんからの{app['type']}申請"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"申請日時: {app['datetime']}")
                            st.write(f"金額: {int(app['amount']):,} P")
                            if pd.notna(app.get('message')) and app.get('message'):
                                st.write(f"メッセージ: {app['message']}")
                        
                        with col2:
                            if st.button("✅ 承認", key=f"approve_{app['app_id']}"):
                                try:
                                    apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
                                    apps_df.loc[apps_df['app_id'] == app['app_id'], 'status'] = '承認済'
                                    apps_df.to_csv(BANK_APPLICATIONS_FILE, index=False)
                                    
                                    if app['type'] == 'loan':
                                        loan_id = f"LOAN_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
                                        
                                        new_loan = pd.DataFrame([{
                                            'loan_id': loan_id,
                                            'datetime': pd.Timestamp.now(),
                                            'lender': st.session_state.username,
                                            'borrower': app['from_user'],
                                            'amount': app['amount'],
                                            'remaining': app['amount'],
                                            'status': 'active',
                                            'due_date': '',  # 期限なし
                                            'last_interest_date': pd.Timestamp.now()
                                        }])
                                        
                                        if os.path.exists(BANK_LOANS_FILE):
                                            loans_df = pd.read_csv(BANK_LOANS_FILE)
                                            loans_df = pd.concat([loans_df, new_loan], ignore_index=True)
                                        else:
                                            loans_df = new_loan
                                        
                                        loans_df.to_csv(BANK_LOANS_FILE, index=False)
                                        
                                        add_notification(app['from_user'], f"✅ {st.session_state.username}さんが融資申請を承認しました！", "success")
                                        
                                        st.success("✅ 融資を承認しました")
                                        
                                    elif app['type'] == 'repayment':
                                        loans_df = pd.read_csv(BANK_LOANS_FILE)
                                        loan_idx = loans_df['loan_id'] == app['loan_id']
                                        
                                        if loan_idx.any():
                                            current_remaining = loans_df.loc[loan_idx, 'remaining'].iloc[0]
                                            new_remaining = max(0, current_remaining - app['amount'])
                                            loans_df.loc[loan_idx, 'remaining'] = new_remaining
                                            
                                            if new_remaining == 0:
                                                loans_df.loc[loan_idx, 'status'] = 'completed'
                                            
                                            loans_df.to_csv(BANK_LOANS_FILE, index=False)
                                            
                                            add_notification(app['from_user'], f"✅ 返済が承認されました！残高: {int(new_remaining):,} P", "success")
                                            
                                            st.success("✅ 返済を承認しました")
                                    
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"承認エラー: {str(e)}")
                            
                            if st.button("❌ 却下", key=f"reject_{app['app_id']}"):
                                try:
                                    apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
                                    apps_df.loc[apps_df['app_id'] == app['app_id'], 'status'] = '却下'
                                    apps_df.to_csv(BANK_APPLICATIONS_FILE, index=False)
                                    
                                    add_notification(app['from_user'], f"❌ {st.session_state.username}さんが申請を却下しました", "error")
                                    
                                    st.warning("申請を却下しました")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"却下エラー: {str(e)}")
            else:
                st.info("📝 承認待ちの申請はありません")
            
            st.markdown("#### 📤 自分の申請状況")
            my_apps = apps_df[(apps_df['from_user'] == st.session_state.username) & (apps_df['status'] == '申込中')]
            
            if not my_apps.empty:
                for _, app in my_apps.iterrows():
                    st.write(f"• {app['to_user']}さんへの{app['type']}申請 - {int(app['amount']):,} P (承認待ち)")
            else:
                st.info("申請中の案件はありません")
        else:
            st.info("📝 申請データがありません")
    
    # 利息一覧タブ（新規追加）
    with tabs[4]:
        st.markdown("### 📈 利息一覧")
        
        # 利息収支サマリー
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"**受取利息累計**\n{int(interest_earned):,} P")
        with col2:
            st.error(f"**支払利息累計**\n{int(interest_paid):,} P")
        with col3:
            net = interest_earned - interest_paid
            if net >= 0:
                st.info(f"**利息収支**\n+{int(net):,} P")
            else:
                st.warning(f"**利息収支**\n{int(net):,} P")
        
        st.markdown("---")
        
        # 利息履歴表示
        if os.path.exists(BANK_TRANSACTIONS_FILE):
            trans_df = pd.read_csv(BANK_TRANSACTIONS_FILE)
            
            # 自分に関連する利息のみ抽出
            my_interest = trans_df[
                ((trans_df['to_user'] == st.session_state.username) | 
                 (trans_df['from_user'] == st.session_state.username)) & 
                (trans_df['type'] == 'interest')
            ].copy()
            
            if not my_interest.empty:
                my_interest = my_interest.sort_values('datetime', ascending=False)
                
                for _, record in my_interest.iterrows():
                    if record['to_user'] == st.session_state.username:
                        # 受取利息
                        st.success(f"📈 **{record['datetime'][:10]}** - {record['from_user']}さんから利息 +{int(record['amount']):,} P")
                        st.caption(f"　　{record.get('notes', '')}")
                    else:
                        # 支払利息
                        st.error(f"📉 **{record['datetime'][:10]}** - {record['to_user']}さんへ利息 -{int(record['amount']):,} P")
                        st.caption(f"　　{record.get('notes', '')}")
                    st.markdown("---")
            else:
                st.info("📝 利息履歴はまだありません（毎月1日に計算されます）")
        else:
            st.info("📝 利息履歴はまだありません")
        
        # 次回利息予測
        st.markdown("#### 💡 次回利息予測（翌月1日）")
        if not loans_df.empty:
            next_earned = 0
            next_paid = 0
            
            # 貸出分の利息
            my_lendings = loans_df[(loans_df['lender'] == st.session_state.username) & (loans_df['status'] == 'active')]
            if not my_lendings.empty:
                for _, loan in my_lendings.iterrows():
                    interest = int(loan['remaining']) * 0.1
                    next_earned += interest
                    st.write(f"• {loan['borrower']}さんから +{int(interest):,} P")
            
            # 借入分の利息
            my_debts = loans_df[(loans_df['borrower'] == st.session_state.username) & (loans_df['status'] == 'active')]
            if not my_debts.empty:
                for _, loan in my_debts.iterrows():
                    interest = int(loan['remaining']) * 0.1
                    next_paid += interest
                    st.write(f"• {loan['lender']}さんへ -{int(interest):,} P")
            
            if next_earned > 0 or next_paid > 0:
                st.markdown("---")
                net_next = next_earned - next_paid
                if net_next >= 0:
                    st.success(f"**翌月の利息収支予測: +{int(net_next):,} P**")
                else:
                    st.error(f"**翌月の利息収支予測: {int(net_next):,} P**")
            else:
                st.info("現在アクティブな融資がありません")
    
    # 履歴タブ
    with tabs[5]:
        st.markdown("### 📊 取引履歴")
        
        all_history = []
        
        # 融資履歴
        if not loans_df.empty:
            for _, loan in loans_df.iterrows():
                if loan['lender'] == st.session_state.username or loan['borrower'] == st.session_state.username:
                    history_type = "貸出" if loan['lender'] == st.session_state.username else "借入"
                    other_user = loan['borrower'] if loan['lender'] == st.session_state.username else loan['lender']
                    
                    all_history.append({
                        '日時': loan['datetime'],
                        'タイプ': history_type,
                        '相手': other_user,
                        '金額': int(loan['amount']),
                        '残高': int(loan['remaining']),
                        '状態': loan['status']
                    })
        
        # 申請履歴
        if not apps_df.empty:
            for _, app in apps_df.iterrows():
                if app['from_user'] == st.session_state.username or app['to_user'] == st.session_state.username:
                    if app['from_user'] == st.session_state.username:
                        app_type = f"{app['type']}申請(送信)"
                        other_user = app['to_user']
                    else:
                        app_type = f"{app['type']}申請(受信)"
                        other_user = app['from_user']
                    
                    all_history.append({
                        '日時': app['datetime'],
                        'タイプ': app_type,
                        '相手': other_user,
                        '金額': int(app['amount']),
                        '残高': '-',
                        '状態': app['status']
                    })
        
        if all_history:
            history_df = pd.DataFrame(all_history)
            history_df = history_df.sort_values('日時', ascending=False)
            
            st.dataframe(
                history_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "金額": st.column_config.NumberColumn("金額", format="%d P"),
                    "残高": st.column_config.TextColumn("残高")
                }
            )
        else:
            st.info("📝 取引履歴がありません")

def community_page():
    """コミュニティページ（修正・改善版）"""
    st.markdown("## 🏆 Community")
    
    # ジャックポットと統計
    col1, col2 = st.columns([3, 2])
    
    with col1:
        current_jackpot = get_current_jackpot()
        st.markdown(f"""
            <div style="background: linear-gradient(45deg, #FFD700, #FFA500); 
                        color: #000; padding: 20px; border-radius: 15px; 
                        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; color: #000;">🎰 現在のジャックポット</h3>
                <h2 style="margin: 10px 0; font-size: 36px; color: #000;">{current_jackpot:,} P</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        try:
            total_play_hours = 0
            total_buyin = 0
            total_players = 0
            
            if os.path.exists(GAME_DATA_FILE):
                game_df = pd.read_csv(GAME_DATA_FILE)
                if 'play_hours' in game_df.columns:
                    total_play_hours = game_df['play_hours'].sum()
                if 'buyin' in game_df.columns:
                    total_buyin = game_df['buyin'].sum()
                total_players = game_df['player'].nunique()
            
            # 背景を半透明の黒に変更、文字を白に
            st.markdown(f"""
                <div style="background: rgba(0, 0, 0, 0.5); 
                            padding: 15px; border-radius: 10px; 
                            backdrop-filter: blur(5px);">
                    <div style="color: white; font-size: 14px; margin-bottom: 8px;">
                        ⏱️ <b>総プレイ時間:</b> {total_play_hours:.1f} 時間
                    </div>
                    <div style="color: white; font-size: 14px; margin-bottom: 8px;">
                        💵 <b>総バイイン:</b> {int(total_buyin):,} P
                    </div>
                    <div style="color: white; font-size: 14px;">
                        👥 <b>アクティブプレイヤー:</b> {total_players} 人
                    </div>
                </div>
            """, unsafe_allow_html=True)
        except:
            st.metric("⏱️ 総プレイ時間", "0.0 時間")
            st.metric("💵 総バイイン", "0 P")
            st.metric("👥 アクティブプレイヤー", "0 人")
    
    # 最新ジャックポット獲得者
    latest_winner = get_latest_jackpot_winner()
    if latest_winner is not None:
        st.markdown(f"""
            <div style="background: linear-gradient(45deg, #FF1493, #FFB6C1); 
                        color: white; padding: 15px; border-radius: 10px; 
                        text-align: center; margin: 20px 0;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="margin: 0; font-size: 18px; font-weight: bold;">
                    🎊 最新ジャックポット獲得者 🎊
                </p>
                <p style="margin: 5px 0; font-size: 20px;">
                    <b>{latest_winner['player']}</b>さん
                </p>
                <p style="margin: 5px 0; font-size: 16px;">
                    {latest_winner['hand_type']} - {int(latest_winner['amount']):,} P
                </p>
                <p style="margin: 5px 0; font-size: 14px; opacity: 0.9;">
                    Hand: {latest_winner.get('hand_cards', 'N/A')} | Board: {latest_winner.get('table_cards', 'N/A')}
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # タブでコンテンツを整理
    tab1, tab2, tab3 = st.tabs(["🏅 ランキング", "📈 統計", "🏆 殿堂"])
    
    with tab1:
        # ランキング
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 🏅 総合収支ランキング")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    
                    if not game_df.empty:
                        player_stats = game_df.groupby('player').agg({
                            'result': 'sum', 
                            'buyin': 'count',
                            'play_hours': 'sum'
                        }).rename(columns={'buyin': 'games'})
                        player_stats = player_stats.sort_values('result', ascending=False)
                        
                        for idx, (player, stats) in enumerate(player_stats.head(10).iterrows(), 1):
                            medal = ""
                            if idx == 1:
                                medal = "🥇"
                                color = "#FFD700"
                            elif idx == 2:
                                medal = "🥈"
                                color = "#C0C0C0"
                            elif idx == 3:
                                medal = "🥉"
                                color = "#CD7F32"
                            else:
                                medal = f"{idx}."
                                color = "#666"
                            
                            profit = int(stats['result'])
                            games = int(stats['games'])
                            avg = profit / games if games > 0 else 0
                            
                            st.markdown(f"""
                                <div style="display: flex; align-items: center; margin: 5px 0;">
                                    <span style="color: {color}; font-size: 20px; width: 40px;">{medal}</span>
                                    <span style="flex: 1;">
                                        <b>{player}</b> - {profit:,} P
                                        <small style="opacity: 0.7;">({games}戦, 平均{int(avg):,}P)</small>
                                    </span>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("まだデータがありません")
                else:
                    st.info("まだデータがありません")
            except:
                st.info("まだデータがありません")
        
        with col2:
            st.markdown("### 🎯 今月のランキング")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    game_df['date'] = pd.to_datetime(game_df['date'])
                    
                    # 今月のデータのみ抽出
                    current_month = pd.Timestamp.now().strftime('%Y-%m')
                    month_df = game_df[game_df['date'].dt.strftime('%Y-%m') == current_month]
                    
                    if not month_df.empty:
                        month_stats = month_df.groupby('player').agg({
                            'result': 'sum',
                            'buyin': 'count'
                        }).rename(columns={'buyin': 'games'})
                        month_stats = month_stats.sort_values('result', ascending=False)
                        
                        for idx, (player, stats) in enumerate(month_stats.head(5).iterrows(), 1):
                            profit = int(stats['result'])
                            games = int(stats['games'])
                            
                            if profit >= 0:
                                st.success(f"{idx}. **{player}** +{profit:,} P ({games}戦)")
                            else:
                                st.error(f"{idx}. **{player}** {profit:,} P ({games}戦)")
                    else:
                        st.info("今月のデータはまだありません")
                else:
                    st.info("まだデータがありません")
            except:
                st.info("まだデータがありません")
    
    with tab2:
        # 統計情報
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 全体統計")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    
                    if not game_df.empty:
                        total_games = len(game_df)
                        total_result = game_df['result'].sum()
                        avg_result = game_df['result'].mean()
                        total_hours = game_df['play_hours'].sum()
                        
                        st.metric("総ゲーム数", f"{total_games} 回")
                        st.metric("総収支", f"{int(total_result):,} P")
                        st.metric("平均収支", f"{int(avg_result):,} P")
                        st.metric("総プレイ時間", f"{total_hours:.1f} 時間")
                        
                        # 勝率
                        wins = (game_df['result'] > 0).sum()
                        win_rate = (wins / total_games * 100) if total_games > 0 else 0
                        st.metric("全体勝率", f"{win_rate:.1f}%")
                    else:
                        st.info("データがありません")
                else:
                    st.info("データがありません")
            except Exception as e:
                st.info("データがありません")
        
        with col2:
            st.markdown("### 🎲 ゲーム傾向")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    
                    if not game_df.empty:
                        # 曜日別の統計
                        game_df['date'] = pd.to_datetime(game_df['date'])
                        game_df['weekday'] = game_df['date'].dt.day_name()
                        
                        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        weekday_jp = ['月', '火', '水', '木', '金', '土', '日']
                        weekday_stats = game_df.groupby('weekday')['result'].agg(['count', 'mean'])
                        
                        st.markdown("**🗓️ 曜日別プレイ頻度**")
                        for day_en, day_jp in zip(weekday_order, weekday_jp):
                            if day_en in weekday_stats.index:
                                count = weekday_stats.loc[day_en, 'count']
                                avg = weekday_stats.loc[day_en, 'mean']
                                bar_width = int(count / len(game_df) * 100)
                                
                                st.markdown(f"""
                                    <div style="margin: 5px 0;">
                                        <span style="width: 30px; display: inline-block;">{day_jp}</span>
                                        <span style="display: inline-block; 
                                                   background: linear-gradient(90deg, #667eea, #764ba2);
                                                   width: {bar_width}%; max-width: 200px;
                                                   padding: 2px 8px; border-radius: 5px;
                                                   color: white; font-size: 12px;">
                                            {int(count)}回
                                        </span>
                                    </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("データがありません")
                else:
                    st.info("データがありません")
            except:
                st.info("データがありません")
    
    with tab3:
        # 殿堂（記録）
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎉 大勝ち記録 TOP5")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    
                    if not game_df.empty:
                        top_wins = game_df.nlargest(5, 'result')
                        for idx, (_, row) in enumerate(top_wins.iterrows(), 1):
                            st.markdown(f"""
                                <div style="background: rgba(40, 167, 69, 0.1); 
                                          padding: 10px; border-radius: 5px; 
                                          margin: 5px 0; border-left: 3px solid #28a745;">
                                    <b>{idx}. {row['player']}</b><br>
                                    <span style="font-size: 20px; color: #28a745;">+{int(row['result']):,} P</span><br>
                                    <small>{row['date']} ({row['play_hours']}時間)</small>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("まだデータがありません")
                else:
                    st.info("まだデータがありません")
            except:
                st.info("まだデータがありません")
        
        with col2:
            st.markdown("### 😱 大負け記録 TOP5")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    
                    if not game_df.empty:
                        top_losses = game_df.nsmallest(5, 'result')
                        for idx, (_, row) in enumerate(top_losses.iterrows(), 1):
                            st.markdown(f"""
                                <div style="background: rgba(220, 53, 69, 0.1); 
                                          padding: 10px; border-radius: 5px; 
                                          margin: 5px 0; border-left: 3px solid #dc3545;">
                                    <b>{idx}. {row['player']}</b><br>
                                    <span style="font-size: 20px; color: #dc3545;">{int(row['result']):,} P</span><br>
                                    <small>{row['date']} ({row['play_hours']}時間)</small>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("まだデータがありません")
                else:
                    st.info("まだデータがありません")
            except:
                st.info("まだデータがありません")

def stats_page():
    """個人統計ページ（グラフ機能追加版）"""
    st.markdown("## 📊 My Stats")
    
    try:
        if os.path.exists(GAME_DATA_FILE):
            game_df = pd.read_csv(GAME_DATA_FILE)
            my_games = game_df[game_df['player'] == st.session_state.username].copy()
            
            if not my_games.empty:
                # データの準備
                my_games['date'] = pd.to_datetime(my_games['date'])
                my_games = my_games.sort_values('date')
                my_games['cumulative'] = my_games['result'].cumsum()
                
                # サマリー統計
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_result = my_games['result'].sum()
                    color = "green" if total_result >= 0 else "red"
                    st.markdown(f"""
                        <div style="background: {color}; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                            <h4>総収支</h4>
                            <h3>{int(total_result):,} P</h3>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    avg_result = my_games['result'].mean()
                    st.metric("平均収支", f"{int(avg_result):,} P")
                
                with col3:
                    total_games = len(my_games)
                    st.metric("プレイ回数", f"{total_games} 回")
                
                with col4:
                    total_hours = my_games['play_hours'].sum()
                    st.metric("総プレイ時間", f"{total_hours:.1f} 時間")
                
                # 詳細統計セクション（グラフより先に表示）
                st.markdown("---")
                st.markdown("### 📈 詳細統計")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("最大勝利", f"{int(my_games['result'].max()):,} P")
                    st.metric("最大敗北", f"{int(my_games['result'].min()):,} P")
                    win_rate = (my_games['result'] > 0).mean() * 100
                    st.metric("勝率", f"{win_rate:.1f}%")
                    
                    # 連勝・連敗
                    my_games['win'] = my_games['result'] > 0
                    streak = 0
                    max_win_streak = 0
                    max_loss_streak = 0
                    current_is_win = None
                    
                    for win in my_games['win']:
                        if current_is_win is None:
                            current_is_win = win
                            streak = 1
                        elif current_is_win == win:
                            streak += 1
                        else:
                            if current_is_win:
                                max_win_streak = max(max_win_streak, streak)
                            else:
                                max_loss_streak = max(max_loss_streak, streak)
                            current_is_win = win
                            streak = 1
                    
                    # 最後のストリークも確認
                    if current_is_win is not None:
                        if current_is_win:
                            max_win_streak = max(max_win_streak, streak)
                        else:
                            max_loss_streak = max(max_loss_streak, streak)
                    
                    st.metric("最大連勝", f"{max_win_streak} 連勝")
                    st.metric("最大連敗", f"{max_loss_streak} 連敗")
                
                with col2:
                    st.metric("総バイイン", f"{int(my_games['buyin'].sum()):,} P")
                    roi = (my_games['result'].sum() / my_games['buyin'].sum() * 100) if my_games['buyin'].sum() > 0 else 0
                    st.metric("ROI", f"{roi:.1f}%")
                    hourly = my_games['result'].sum() / my_games['play_hours'].sum() if my_games['play_hours'].sum() > 0 else 0
                    st.metric("時給", f"{int(hourly):,} P/h")
                    
                    # 直近のトレンド
                    if len(my_games) >= 5:
                        recent_5 = my_games.tail(5)['result'].sum()
                        recent_10 = my_games.tail(10)['result'].sum() if len(my_games) >= 10 else recent_5
                        
                        st.metric("直近5戦", f"{int(recent_5):,} P")
                        if len(my_games) >= 10:
                            st.metric("直近10戦", f"{int(recent_10):,} P")
                
                # グラフセクション（詳細統計の後に表示）
                st.markdown("---")
                st.markdown("### 📊 収支チャート")
                
                if PLOTLY_AVAILABLE:
                    # タブでグラフを分ける
                    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📊 累積収支", "📈 日別収支", "📅 月別集計"])
                    
                    with chart_tab1:
                        # 累積収支グラフ
                        fig_cumulative = go.Figure()
                        
                        # メインの累積収支ライン
                        fig_cumulative.add_trace(go.Scatter(
                            x=my_games['date'],
                            y=my_games['cumulative'],
                            mode='lines+markers',
                            name='累積収支',
                            line=dict(color='#667eea', width=3),
                            marker=dict(size=8, color='#764ba2'),
                            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>累積: %{y:,.0f} P<extra></extra>'
                        ))
                        
                        # ゼロライン
                        fig_cumulative.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                        
                        # プラス域を緑、マイナス域を赤で塗りつぶし
                        fig_cumulative.add_trace(go.Scatter(
                            x=my_games['date'],
                            y=my_games['cumulative'],
                            fill='tozeroy',
                            fillcolor='rgba(40, 167, 69, 0.2)',
                            line=dict(width=0),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        
                        fig_cumulative.update_layout(
                            title="累積収支推移",
                            xaxis_title="日付",
                            yaxis_title="累積収支 (P)",
                            hovermode='x unified',
                            height=400,
                            template="plotly_white",
                            font=dict(size=12),
                            margin=dict(l=50, r=50, t=50, b=50)
                        )
                        
                        st.plotly_chart(fig_cumulative, use_container_width=True)
                        
                        # 統計情報
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            max_cumulative = my_games['cumulative'].max()
                            st.info(f"**最高到達点:** {int(max_cumulative):,} P")
                        with col2:
                            min_cumulative = my_games['cumulative'].min()
                            st.info(f"**最低到達点:** {int(min_cumulative):,} P")
                        with col3:
                            current = my_games['cumulative'].iloc[-1]
                            st.info(f"**現在:** {int(current):,} P")
                    
                    with chart_tab2:
                        # 日別収支グラフ（棒グラフ）
                        colors = ['green' if x >= 0 else 'red' for x in my_games['result']]
                        
                        fig_daily = go.Figure(data=[
                            go.Bar(
                                x=my_games['date'],
                                y=my_games['result'],
                                marker_color=colors,
                                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>収支: %{y:,.0f} P<extra></extra>'
                            )
                        ])
                        
                        fig_daily.update_layout(
                            title="日別収支",
                            xaxis_title="日付",
                            yaxis_title="収支 (P)",
                            height=400,
                            template="plotly_white",
                            showlegend=False,
                            margin=dict(l=50, r=50, t=50, b=50)
                        )
                        
                        st.plotly_chart(fig_daily, use_container_width=True)
                        
                        # 勝敗統計
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            wins = (my_games['result'] > 0).sum()
                            st.success(f"**勝利日数:** {wins} 日")
                        with col2:
                            losses = (my_games['result'] < 0).sum()
                            st.error(f"**敗北日数:** {losses} 日")
                        with col3:
                            draws = (my_games['result'] == 0).sum()
                            st.info(f"**引き分け:** {draws} 日")
                    
                    with chart_tab3:
                        # 月別集計グラフ
                        my_games['year_month'] = my_games['date'].dt.to_period('M')
                        monthly_stats = my_games.groupby('year_month').agg({
                            'result': 'sum',
                            'play_hours': 'sum',
                            'buyin': 'count'
                        }).rename(columns={'buyin': 'games'})
                        monthly_stats.index = monthly_stats.index.to_timestamp()
                        
                        # 月別収支の棒グラフ
                        colors_monthly = ['green' if x >= 0 else 'red' for x in monthly_stats['result']]
                        
                        fig_monthly = go.Figure()
                        
                        fig_monthly.add_trace(go.Bar(
                            x=monthly_stats.index,
                            y=monthly_stats['result'],
                            name='月間収支',
                            marker_color=colors_monthly,
                            hovertemplate='<b>%{x|%Y年%m月}</b><br>収支: %{y:,.0f} P<extra></extra>'
                        ))
                        
                        fig_monthly.update_layout(
                            title="月別収支",
                            xaxis_title="月",
                            yaxis_title="収支 (P)",
                            height=400,
                            template="plotly_white",
                            showlegend=False,
                            margin=dict(l=50, r=50, t=50, b=50)
                        )
                        
                        st.plotly_chart(fig_monthly, use_container_width=True)
                        
                        # 月別詳細テーブル
                        st.markdown("#### 📋 月別詳細")
                        monthly_display = monthly_stats.copy()
                        monthly_display['平均収支'] = monthly_display['result'] / monthly_display['games']
                        monthly_display['時給'] = monthly_display['result'] / monthly_display['play_hours']
                        monthly_display = monthly_display.sort_index(ascending=False)
                        
                        # 表示用に整形
                        monthly_display_formatted = pd.DataFrame({
                            '年月': monthly_display.index.strftime('%Y年%m月'),
                            '収支': [f"{int(x):,} P" for x in monthly_display['result']],
                            'ゲーム数': monthly_display['games'],
                            'プレイ時間': [f"{x:.1f}h" for x in monthly_display['play_hours']],
                            '平均収支': [f"{int(x):,} P" for x in monthly_display['平均収支']],
                            '時給': [f"{int(x):,} P/h" for x in monthly_display['時給']]
                        })
                        
                        st.dataframe(monthly_display_formatted, use_container_width=True, hide_index=True)
                
                else:
                    # Plotlyが利用できない場合の簡易表示
                    st.warning("グラフ表示にはPlotlyが必要です。`pip install plotly`でインストールしてください。")
                    
                    # 代替として最近10件の収支を表示
                    st.markdown("#### 📊 最近の収支（10件）")
                    recent_games = my_games.tail(10).sort_values('date', ascending=False)
                    for _, game in recent_games.iterrows():
                        if game['result'] >= 0:
                            st.success(f"{game['date'].strftime('%Y-%m-%d')}: +{int(game['result']):,} P (累積: {int(game['cumulative']):,} P)")
                        else:
                            st.error(f"{game['date'].strftime('%Y-%m-%d')}: {int(game['result']):,} P (累積: {int(game['cumulative']):,} P)")
                
            else:
                st.info("📝 まだゲーム履歴がありません")
        else:
            st.info("📝 まだゲーム履歴がありません")
            
    except Exception as e:
        st.error(f"統計エラー: {str(e)}")

def admin_page():
    """管理者ページ（完全実装）"""
    st.markdown("## ⚙️ 管理者パネル")
    
    tab1, tab2, tab3 = st.tabs(["👥 ユーザー管理", "🎰 ジャックポット管理", "🗑️ データ管理"])
    
    with tab1:
        st.markdown("### 👥 ユーザー管理")
        
        users_df = load_users()
        
        # ユーザー追加
        with st.expander("➕ 新規ユーザー追加"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_username = st.text_input("ユーザー名", key="new_user")
            with col2:
                new_password = st.text_input("パスワード", type="password", key="new_pass")
            with col3:
                new_role = st.selectbox("権限", ["player", "admin"], key="new_role")
            
            if st.button("追加", key="add_user"):
                if new_username and new_password:
                    if new_username not in users_df['username'].values:
                        new_user = pd.DataFrame([{
                            'username': new_username,
                            'password': new_password,
                            'role': new_role,
                            'active': True
                        }])
                        users_df = pd.concat([users_df, new_user], ignore_index=True)
                        save_users(users_df)
                        st.success(f"✅ ユーザー {new_username} を追加しました")
                        st.rerun()
                    else:
                        st.error("このユーザー名は既に存在します")
                else:
                    st.error("ユーザー名とパスワードを入力してください")
        
        # ユーザー編集
        edited_df = st.data_editor(
            users_df,
            column_config={
                "username": st.column_config.TextColumn("ユーザー名", disabled=True),
                "password": st.column_config.TextColumn("パスワード"),
                "role": st.column_config.SelectboxColumn("権限", options=["admin", "player"]),
                "active": st.column_config.CheckboxColumn("アクティブ")
            },
            use_container_width=True,
            hide_index=True,
            num_rows="fixed"
        )
        
        if st.button("💾 変更を保存", use_container_width=True):
            save_users(edited_df)
            st.success("✅ ユーザー情報を更新しました")
            st.rerun()
    
    with tab2:
        st.markdown("### 🎰 ジャックポット管理")
        
        current_jackpot = get_current_jackpot()
        st.metric("現在のジャックポット", f"{current_jackpot:,} P")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💰 金額管理")
            jp_amount = st.number_input("金額変更 (P)", step=1, value=0)
            jp_note = st.text_input("備考")
            
            if st.button("💰 金額を追加/削減"):
                if jp_amount != 0:
                    try:
                        df = pd.read_csv(JACKPOT_DATA_FILE)
                        
                        new_total = current_jackpot + jp_amount
                        
                        new_data = pd.DataFrame([{
                            'datetime': pd.Timestamp.now(),
                            'type': 'add' if jp_amount > 0 else 'subtract',
                            'amount': jp_amount,
                            'total': new_total,
                            'admin': st.session_state.username,
                            'notes': jp_note
                        }])
                        
                        df = pd.concat([df, new_data], ignore_index=True)
                        df.to_csv(JACKPOT_DATA_FILE, index=False)
                        
                        st.success(f"✅ ジャックポットを更新しました: {new_total:,} P")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"更新エラー: {str(e)}")
        
        with col2:
            st.markdown("#### 🎊 当選者登録")
            
            users_df = load_users()
            winner = st.selectbox("当選者", users_df['username'].tolist())
            hand_type = st.selectbox("役", ["Royal Flush", "Straight Flush", "Four of a Kind", "Full House"])
            hand_cards = st.text_input("ハンドカード", placeholder="例: A♠K♠")
            table_cards = st.text_input("ボードカード", placeholder="例: Q♠J♠10♠")
            payout = st.number_input("支払額 (P)", min_value=0, value=current_jackpot)
            
            if st.button("🎊 当選者を登録"):
                if winner and payout > 0:
                    try:
                        # 当選者データを保存
                        winners_df = pd.read_csv(JACKPOT_WINNERS_FILE) if os.path.exists(JACKPOT_WINNERS_FILE) else pd.DataFrame()
                        
                        new_winner = pd.DataFrame([{
                            'datetime': pd.Timestamp.now(),
                            'date': datetime.date.today(),
                            'player': winner,
                            'hand_type': hand_type,
                            'hand_cards': hand_cards,
                            'table_cards': table_cards,
                            'amount': payout,
                            'paid': False
                        }])
                        
                        winners_df = pd.concat([winners_df, new_winner], ignore_index=True)
                        winners_df.to_csv(JACKPOT_WINNERS_FILE, index=False)
                        
                        # ジャックポットをリセット
                        jp_df = pd.read_csv(JACKPOT_DATA_FILE)
                        new_jp = pd.DataFrame([{
                            'datetime': pd.Timestamp.now(),
                            'type': 'payout',
                            'amount': -payout,
                            'total': 0,
                            'admin': st.session_state.username,
                            'notes': f"{winner}さんが{hand_type}で獲得"
                        }])
                        
                        jp_df = pd.concat([jp_df, new_jp], ignore_index=True)
                        jp_df.to_csv(JACKPOT_DATA_FILE, index=False)
                        
                        # 通知
                        add_notification(
                            winner,
                            f"🎊 おめでとうございます！ジャックポット{payout:,} Pを獲得しました！",
                            "success"
                        )
                        
                        st.balloons()
                        st.success(f"✅ {winner}さんのジャックポット獲得を登録しました！")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"登録エラー: {str(e)}")
    
    with tab3:
        st.markdown("### 🗑️ データ管理")
        
        st.warning("⚠️ データ削除は取り消せません。実行前に必ずバックアップを取ってください。")
        
        # バックアップ機能
        st.markdown("#### 💾 バックアップ")
        
        if st.button("📥 全データをバックアップ"):
            try:
                backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                
                with zipfile.ZipFile(backup_name, 'w') as zipf:
                    for file in [GAME_DATA_FILE, BANK_LOANS_FILE, BANK_APPLICATIONS_FILE, 
                               BANK_TRANSACTIONS_FILE, JACKPOT_DATA_FILE, JACKPOT_WINNERS_FILE,
                               USERS_DATA_FILE, NOTIFICATIONS_FILE]:
                        if os.path.exists(file):
                            zipf.write(file)
                
                st.success(f"✅ バックアップを作成しました: {backup_name}")
                
                with open(backup_name, "rb") as file:
                    st.download_button(
                        label="📥 バックアップをダウンロード",
                        data=file,
                        file_name=backup_name,
                        mime="application/zip"
                    )
                    
            except Exception as e:
                st.error(f"バックアップエラー: {str(e)}")
        
        st.markdown("#### 🗑️ データ削除")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎮 ゲームデータを削除", use_container_width=True):
                if st.checkbox("本当に削除しますか？", key="del_game_confirm"):
                    try:
                        if os.path.exists(GAME_DATA_FILE):
                            os.remove(GAME_DATA_FILE)
                            init_data()
                            st.success("ゲームデータを削除しました")
                            st.rerun()
                    except Exception as e:
                        st.error(f"削除エラー: {str(e)}")
            
            if st.button("💰 P-BANKデータを削除", use_container_width=True):
                if st.checkbox("本当に削除しますか？", key="del_bank_confirm"):
                    try:
                        for file in [BANK_LOANS_FILE, BANK_APPLICATIONS_FILE, BANK_TRANSACTIONS_FILE]:
                            if os.path.exists(file):
                                os.remove(file)
                        init_data()
                        st.success("P-BANKデータを削除しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除エラー: {str(e)}")
        
        with col2:
            if st.button("🎰 ジャックポットデータを削除", use_container_width=True):
                if st.checkbox("本当に削除しますか？", key="del_jp_confirm"):
                    try:
                        for file in [JACKPOT_DATA_FILE, JACKPOT_WINNERS_FILE]:
                            if os.path.exists(file):
                                os.remove(file)
                        init_data()
                        st.success("ジャックポットデータを削除しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除エラー: {str(e)}")
            
            if st.button("⚠️ 全データを初期化", use_container_width=True):
                if st.checkbox("本当に全データを初期化しますか？", key="del_all_confirm"):
                    if st.text_input("確認のため「DELETE ALL」と入力してください", key="del_all_text") == "DELETE ALL":
                        try:
                            for file in [GAME_DATA_FILE, BANK_LOANS_FILE, BANK_APPLICATIONS_FILE,
                                       BANK_TRANSACTIONS_FILE, JACKPOT_DATA_FILE, JACKPOT_WINNERS_FILE,
                                       NOTIFICATIONS_FILE]:
                                if os.path.exists(file):
                                    os.remove(file)
                            
                            users_df = pd.DataFrame(DEFAULT_USERS)
                            users_df.to_csv(USERS_DATA_FILE, index=False)
                            
                            init_data()
                            st.success("全データを初期化しました")
                            st.session_state.logged_in = False
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"初期化エラー: {str(e)}")

def main_app():
    """メインアプリケーション"""
    notifications = get_notifications(st.session_state.username)
    notification_badge = f" 🔴{len(notifications)}" if not notifications.empty else ""
    
    st.markdown(f"""
        <div class="main-header">
            <h1 style="color: white; font-size: 36px; margin: 0;">🃏 We Are Pretty Cure! 🃏</h1>
            <p style="color: rgba(255, 255, 255, 0.9);">ようこそ、{st.session_state.username} さん！{notification_badge}</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([4, 1, 1])
    with col3:
        if st.button("🚪 ログアウト"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
    
    st.markdown("### 📱 メインメニュー")
    
    # P-BANKの承認待ち件数を取得
    pending_count = 0
    try:
        if os.path.exists(BANK_APPLICATIONS_FILE):
            apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
            pending_count = len(apps_df[(apps_df['to_user'] == st.session_state.username) & (apps_df['status'] == '申込中')])
    except:
        pass
    
    pbank_badge = f" ({pending_count})" if pending_count > 0 else ""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎮 ゲームレポート", use_container_width=True):
            st.session_state.page = "game_report"
            st.rerun()
    
    with col2:
        if st.button(f"💰 P-BANK{pbank_badge}", use_container_width=True):
            st.session_state.page = "pbank"
            st.rerun()
    
    with col3:
        if st.button("🏆 Community", use_container_width=True):
            st.session_state.page = "community"
            st.rerun()
    
    with col4:
        if st.button("📊 My Stats", use_container_width=True):
            st.session_state.page = "stats"
            st.rerun()
    
    if st.session_state.role == 'admin':
        st.markdown("### 🔧 管理者メニュー")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⚙️ 管理", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()
    
    st.markdown("---")
    
    # ページ表示
    if st.session_state.page == "game_report":
        game_report_page()
    elif st.session_state.page == "pbank":
        pbank_page()
    elif st.session_state.page == "community":
        community_page()
    elif st.session_state.page == "stats":
        stats_page()
    elif st.session_state.page == "admin" and st.session_state.role == 'admin':
        admin_page()

def main():
    """メインアプリケーション実行"""
    init_data()
    init_session_state()
    
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
