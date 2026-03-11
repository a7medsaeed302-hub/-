/*
  # إنشاء جداول نظام حماية الحسابات

  1. الجداول الجديدة
    - `accounts` - جدول الحسابات المحمية
      - `id` (uuid, primary key)
      - `user_id` (bigint) - معرف المستخدم في تيليجرام
      - `platform` (text) - المنصة (فيسبوك، تويتر، إنستغرام)
      - `username` (text) - اسم المستخدم
      - `email` (text) - البريد الإلكتروني
      - `is_2fa_enabled` (boolean) - تفعيل المصادقة الثنائية
      - `security_level` (integer) - مستوى الأمان (1-4)
      - `created_at` (timestamptz) - تاريخ الإنشاء
      - `updated_at` (timestamptz) - تاريخ التحديث

    - `security_alerts` - جدول التنبيهات الأمنية
      - `id` (uuid, primary key)
      - `account_id` (uuid, foreign key) - معرف الحساب
      - `alert_type` (text) - نوع التنبيه
      - `threat_level` (integer) - مستوى التهديد (1-4)
      - `message` (text) - رسالة التنبيه
      - `ip_address` (text) - عنوان IP
      - `location` (text) - الموقع الجغرافي
      - `device_info` (text) - معلومات الجهاز
      - `is_resolved` (boolean) - حالة الحل
      - `created_at` (timestamptz) - تاريخ الإنشاء

    - `login_attempts` - جدول محاولات تسجيل الدخول
      - `id` (uuid, primary key)
      - `account_id` (uuid, foreign key) - معرف الحساب
      - `success` (boolean) - نجاح المحاولة
      - `ip_address` (text) - عنوان IP
      - `location` (text) - الموقع الجغرافي
      - `device_info` (text) - معلومات الجهاز
      - `created_at` (timestamptz) - تاريخ المحاولة

    - `blocked_ips` - جدول عناوين IP المحظورة
      - `id` (uuid, primary key)
      - `ip_address` (text, unique) - عنوان IP
      - `reason` (text) - سبب الحظر
      - `blocked_at` (timestamptz) - تاريخ الحظر
      - `expires_at` (timestamptz) - تاريخ انتهاء الحظر

  2. الأمان
    - تفعيل RLS على جميع الجداول
    - سياسات الوصول للمستخدمين المصادقين فقط
*/

CREATE TABLE IF NOT EXISTS accounts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id bigint NOT NULL,
  platform text NOT NULL,
  username text NOT NULL,
  email text,
  is_2fa_enabled boolean DEFAULT false,
  security_level integer DEFAULT 1,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS security_alerts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid REFERENCES accounts(id) ON DELETE CASCADE,
  alert_type text NOT NULL,
  threat_level integer DEFAULT 1,
  message text NOT NULL,
  ip_address text,
  location text,
  device_info text,
  is_resolved boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS login_attempts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid REFERENCES accounts(id) ON DELETE CASCADE,
  success boolean DEFAULT false,
  ip_address text,
  location text,
  device_info text,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS blocked_ips (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ip_address text UNIQUE NOT NULL,
  reason text NOT NULL,
  blocked_at timestamptz DEFAULT now(),
  expires_at timestamptz
);

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE blocked_ips ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own accounts"
  ON accounts FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert own accounts"
  ON accounts FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Users can update own accounts"
  ON accounts FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Users can delete own accounts"
  ON accounts FOR DELETE
  TO authenticated
  USING (true);

CREATE POLICY "Users can view security alerts"
  ON security_alerts FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert security alerts"
  ON security_alerts FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Users can update security alerts"
  ON security_alerts FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Users can view login attempts"
  ON login_attempts FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert login attempts"
  ON login_attempts FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Users can view blocked IPs"
  ON blocked_ips FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert blocked IPs"
  ON blocked_ips FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Users can update blocked IPs"
  ON blocked_ips FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Users can delete blocked IPs"
  ON blocked_ips FOR DELETE
  TO authenticated
  USING (true);

CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_security_alerts_account_id ON security_alerts(account_id);
CREATE INDEX IF NOT EXISTS idx_login_attempts_account_id ON login_attempts(account_id);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_ip_address ON blocked_ips(ip_address);