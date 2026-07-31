#include <jni.h>
#include <string>
#include <memory>
#include <cstdint>
#include <vector>
#include <pjlib.h>
#include <pjmedia.h>
#include <pjmedia_audiodev.h>
#include <pjsua.h>
#include <oboe/Oboe.h>
#include <android/log.h>

#define LOG_TAG "ZeeGate-Native"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGD(...) __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)

/**
 * Pushes raw PCM data from Oboe into a PJSIP media port.
 * @param port The PJSIP media port (sink)
 * @param pcmData The PCM samples from Oboe
 * @param frameCount Number of frames
 * @param channelCount Number of channels
 */
void pushOboeSamplesToPjsip(pjmedia_port *port, const float *pcmData, int32_t frameCount, int32_t channelCount) {
    if (!port || !pcmData) return;

    // Use a stack-based buffer for standard frame sizes (e.g., 20ms at 48kHz = 960 samples)
    // PJSIP typically uses 10ms or 20ms frames.
    const int32_t MAX_SAMPLES = 2048;
    int32_t totalSamples = frameCount * channelCount;

    if (totalSamples > MAX_SAMPLES) return; // Safety check

    pj_int16_t samples[MAX_SAMPLES];

    for (int32_t i = 0; i < totalSamples; ++i) {
        // Convert Float (-1.0 to 1.0) to Short (-32768 to 32767) with clipping
        float sample = pcmData[i] * 32767.0f;
        if (sample > 32767.0f) sample = 32767.0f;
        else if (sample < -32768.0f) sample = -32768.0f;
        samples[i] = static_cast<pj_int16_t>(sample);
    }

    pjmedia_frame frame;
    pj_bzero(&frame, sizeof(frame));
    frame.type = PJMEDIA_FRAME_TYPE_AUDIO;
    frame.buf = samples;
    frame.size = totalSamples * sizeof(pj_int16_t);

    // Push frame into the PJSIP port
    pjmedia_port_put_frame(port, &frame);
}

class AudioEngine : public oboe::AudioStreamCallback {
public:
    AudioEngine() = default;

    oboe::Result start() {
        if (mStream) return oboe::Result::OK;

        oboe::AudioStreamBuilder builder;
        builder.setDirection(oboe::Direction::Input) // Capture mic audio
                ->setPerformanceMode(oboe::PerformanceMode::LowLatency)
                ->setSharingMode(oboe::SharingMode::Exclusive)
                ->setFormat(oboe::AudioFormat::Float)
                ->setChannelCount(oboe::ChannelCount::Mono) // Usually mono for SIP
                ->setCallback(this);

        oboe::Result result = builder.openStream(mStream);
        if (result != oboe::Result::OK) {
            LOGE("Error opening stream: %s", oboe::convertToText(result));
            return result;
        }

        result = mStream->requestStart();
        if (result != oboe::Result::OK) {
            LOGE("Error starting stream: %s", oboe::convertToText(result));
        }
        return result;
    }

    void stop() {
        if (mStream) {
            mStream->stop();
            mStream->close();
            mStream.reset();
        }
    }

    void setPjsipPort(pjmedia_port *port) {
        mPjsipPort = port;
    }

    // Get telemetry data from the engine
    std::string getTelemetry() {
        if (!mStream) return "Engine: Offline";

        char buffer[128];
        snprintf(buffer, sizeof(buffer), "Engine: Online, Frames: %lld, State: %s",
                 (long long)mStream->getFramesRead(),
                 oboe::convertToText(mStream->getState()));
        return std::string(buffer);
    }

    oboe::DataCallbackResult onAudioReady(oboe::AudioStream *audioStream, void *audioData, int32_t numFrames) override {
        // audioData contains the captured samples (input direction)
        auto *pcmData = static_cast<const float *>(audioData);
        int32_t channelCount = audioStream->getChannelCount();

        // If we have a PJSIP port, push samples to it
        if (mPjsipPort) {
            pushOboeSamplesToPjsip(mPjsipPort, pcmData, numFrames, channelCount);
        }

        return oboe::DataCallbackResult::Continue;
    }

private:
    std::shared_ptr<oboe::AudioStream> mStream;
    pjmedia_port *mPjsipPort = nullptr;
};

static AudioEngine engine;

// PJSIP UA instance
static bool pjsip_initialized = false;

extern "C" JNIEXPORT jboolean JNICALL
Java_com_example_zeegate_MainActivity_initPjsip(JNIEnv *env, jobject thiz, jstring server, jstring user, jstring pass) {
    (void)thiz;
    if (pjsip_initialized) return JNI_TRUE;

    const char *pj_server = env->GetStringUTFChars(server, nullptr);
    const char *pj_user = env->GetStringUTFChars(user, nullptr);
    const char *pj_pass = env->GetStringUTFChars(pass, nullptr);

    pj_status_t status;

    // Create pjsua
    status = pjsua_create();
    if (status != PJ_SUCCESS) return JNI_FALSE;

    // Configs
    pjsua_config ua_cfg;
    pjsua_logging_config log_cfg;
    pjsua_media_config media_cfg;

    pjsua_config_default(&ua_cfg);
    pjsua_logging_config_default(&log_cfg);
    pjsua_media_config_default(&media_cfg);

    log_cfg.level = 4;
    log_cfg.cb = [](int level, const char *data, int len) {
        (void)level; (void)len;
        __android_log_print(ANDROID_LOG_DEBUG, "PJSIP", "%s", data);
    };

    status = pjsua_init(&ua_cfg, &log_cfg, &media_cfg);
    if (status != PJ_SUCCESS) return JNI_FALSE;

    // UDP Transport
    pjsua_transport_config trans_cfg;
    pjsua_transport_config_default(&trans_cfg);
    status = pjsua_transport_create(PJSIP_TRANSPORT_UDP, &trans_cfg, NULL);
    if (status != PJ_SUCCESS) return JNI_FALSE;

    // Start pjsua
    status = pjsua_start();
    if (status != PJ_SUCCESS) return JNI_FALSE;

    // Add SIP Account
    pjsua_acc_config acc_cfg;
    pjsua_acc_config_default(&acc_cfg);
    char id[128], reg[128];
    snprintf(id, sizeof(id), "sip:%s@%s", pj_user, pj_server);
    snprintf(reg, sizeof(reg), "sip:%s", pj_server);

    acc_cfg.id = pj_str(id);
    acc_cfg.reg_uri = pj_str(reg);
    acc_cfg.cred_count = 1;
    acc_cfg.cred_info[0].realm = pj_str((char*)"*");
    acc_cfg.cred_info[0].scheme = pj_str((char*)"digest");
    acc_cfg.cred_info[0].username = pj_str((char*)pj_user);
    acc_cfg.cred_info[0].data_type = PJSIP_CRED_DATA_PLAIN_PASSWD;
    acc_cfg.cred_info[0].data = pj_str((char*)pj_pass);

    pjsua_acc_id acc_id;
    status = pjsua_acc_add(&acc_cfg, PJ_TRUE, &acc_id);

    env->ReleaseStringUTFChars(server, pj_server);
    env->ReleaseStringUTFChars(user, pj_user);
    env->ReleaseStringUTFChars(pass, pj_pass);

    if (status == PJ_SUCCESS) {
        pjsip_initialized = true;
        return JNI_TRUE;
    }
    return JNI_FALSE;
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_zeegate_MainActivity_stringFromJNI(JNIEnv *env, jobject thiz) {
    (void)thiz;
    if (env == nullptr) return nullptr;

    oboe::Result result = engine.start();
    std::string status = "Oboe Stream: ";
    status += oboe::convertToText(result);

    if (result == oboe::Result::OK) {
        LOGD("Oboe stream started successfully");
    } else {
        LOGE("Failed to start Oboe stream");
    }

    return env->NewStringUTF(status.c_str());
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_zeegate_MainActivity_getEngineTelemetry(JNIEnv *env, jobject thiz) {
    (void)thiz;
    return env->NewStringUTF(engine.getTelemetry().c_str());
}
