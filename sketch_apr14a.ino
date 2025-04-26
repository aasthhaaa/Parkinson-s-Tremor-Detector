#include <Wire.h>
#include <MPU6050.h>
#include <LiquidCrystal_I2C.h>

MPU6050 mpu;
LiquidCrystal_I2C lcd(0x27, 16, 2); // Use I2C address

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22); // SDA = D21, SCL = D22

  mpu.initialize();
  if (!mpu.testConnection()) {
    Serial.println("MPU6050 not found!");
    while (1);
  }

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print(" Parkinson's ");
  lcd.setCursor(0, 1);
  lcd.print("  Detector...  ");
  delay(2000);
  lcd.clear();
}

void loop() {
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  // Send sensor data to PC
  Serial.print(ax); Serial.print(",");
  Serial.print(ay); Serial.print(",");
  Serial.print(az); Serial.print(",");
  Serial.print(gx); Serial.print(",");
  Serial.print(gy); Serial.print(",");
  Serial.println(gz);

  // Check for PC prediction
  if (Serial.available()) {
    // Flush buffer to get most recent value
    while (Serial.available() > 1) Serial.read();  
    char result = Serial.read();

    Serial.print("Received from PC: ");
    Serial.println(result);  

    lcd.clear();
    lcd.setCursor(0, 0);
    if (result == '1') {
      lcd.print(" Tremor Detected ");
    } else if (result == '0') {
      lcd.print(" Normal Motion   ");
    } else {
      lcd.print("Unknown Data");
    }
  }

  delay(20);  // 50 Hz sampling
}