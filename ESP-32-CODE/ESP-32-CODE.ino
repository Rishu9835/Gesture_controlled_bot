#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

//WiFi Credentials
const char* ssid = "YOUR-WIFI-NAME";
const char* password = "WIFI-PASSWORD";

//Motor Pins
#define IN1 15
#define IN2 14
#define IN3 2
#define IN4 4

//for built-in LED
#define LED_PIN 33

//Camera Pins for AI thinker
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

httpd_handle_t stream_httpd = NULL;
WiFiServer commandServer(80);

//Motor Control
void setupMotors() {
  ledcSetup(0, 1000, 8); 
  ledcSetup(1, 1000, 8);
  ledcSetup(2, 1000, 8);
  ledcSetup(3, 1000, 8);
  ledcAttachPin(IN1, 0);
  ledcAttachPin(IN2, 1);
  ledcAttachPin(IN3, 2);
  ledcAttachPin(IN4, 3);
  pinMode(LED_PIN, OUTPUT);
  stopMotors();
}

void stopMotors() {
  ledcWrite(0, 0); ledcWrite(1, 0);
  ledcWrite(2, 0); ledcWrite(3, 0);
  digitalWrite(LED_PIN, LOW);
}

void moveForward(uint8_t speed) {
  ledcWrite(0, speed); ledcWrite(1, 0);
  ledcWrite(2, speed); ledcWrite(3, 0);
  digitalWrite(LED_PIN, HIGH);
}

void moveBackward(uint8_t speed) {
  ledcWrite(0, 0); ledcWrite(1, speed);
  ledcWrite(2, 0); ledcWrite(3, speed);
  digitalWrite(LED_PIN, HIGH);
}

void turnLeft(uint8_t speed) {
  ledcWrite(0, 0); ledcWrite(1, speed);
  ledcWrite(2, speed); ledcWrite(3, 0);
  digitalWrite(LED_PIN, HIGH);
}

void turnRight(uint8_t speed) {
  ledcWrite(0, speed); ledcWrite(1, 0);
  ledcWrite(2, 0); ledcWrite(3, speed);
  digitalWrite(LED_PIN, HIGH);
}

//Camera Stream Handler
esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = ESP_OK;

  res = httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      return ESP_FAIL;
    }

    char buf[64];
    snprintf(buf, sizeof(buf),
             "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",
             fb->len);
    if (httpd_resp_send_chunk(req, buf, strlen(buf)) != ESP_OK ||
        httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len) != ESP_OK ||
        httpd_resp_send_chunk(req, "\r\n", 2) != ESP_OK) {
      esp_camera_fb_return(fb);
      break;
    }
    esp_camera_fb_return(fb);
    vTaskDelay(50 / portTICK_PERIOD_MS);
  }

  return res;
}

//Start Stream Server
void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 81;
  config.stack_size = 8192;  // Prevent stack overflow crash

  httpd_uri_t stream_uri = {
    .uri       = "/",
    .method    = HTTP_GET,
    .handler   = stream_handler,
    .user_ctx  = NULL
  };

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
    Serial.println("✅ Camera stream ready at /");
  } else {
    Serial.println("❌ Failed to start camera server");
  }
}

//Command Endpoint
void handleClientCommands() {
  WiFiClient client = commandServer.available();
  if (client && client.connected()) {
    String req = client.readStringUntil('\r');
    client.flush();

    if (req.indexOf("GET /move?cmd=") >= 0) {
      char dir = 'S';
      int level = 5; // default speed level
      int idx = req.indexOf("cmd=");
      if (idx >= 0 && idx + 5 <= req.length()) {
        dir = req.charAt(idx + 4);
        if (isDigit(req.charAt(idx + 5))) {
          level = req.charAt(idx + 5) - '0';
        }
      }

      uint8_t pwm = map(level, 0, 9, 0, 255);

      if      (dir == 'F') moveForward(pwm);
      else if (dir == 'B') moveBackward(pwm);
      else if (dir == 'L') turnLeft(pwm);
      else if (dir == 'R') turnRight(pwm);
      else stopMotors();

      client.print("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK");
    }

    delay(5);
    client.stop();
  }
}

//Setup
void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  setupMotors();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;
  config.pin_xclk = 0;
  config.pin_pclk = 22;
  config.pin_vsync = 25;
  config.pin_href = 23;
  config.pin_sscb_sda = 26;
  config.pin_sscb_scl = 27;
  config.pin_pwdn = 32;
  config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x", err);
    return;
  }

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }

  Serial.println("\n✅ WiFi connected");
  Serial.print("📶 IP address: ");
  Serial.println(WiFi.localIP());

  startCameraServer();   // Stream on port 81
  commandServer.begin(); // Movement control on port 80
}

//Loop to responds for comands repeatedly
void loop() {
  handleClientCommands();
}
