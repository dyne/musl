#include <alsa/asoundlib.h>

int main(void) {
    snd_config_t *config;
    if (snd_config_load_string(&config, "pcm.smoke { type null }", 0) < 0) return 1;
    snd_pcm_t *pcm;
    int result = snd_pcm_open_lconf(&pcm, "smoke", SND_PCM_STREAM_PLAYBACK, 0, config);
    snd_config_delete(config);
    if (result < 0) return 2;
    return snd_pcm_close(pcm) < 0;
}
