#include <curl/curl.h>
#include <span>
#include <thread>

int main() {
    if (curl_global_init(CURL_GLOBAL_DEFAULT) != CURLE_OK) return 1;
    CURL* handle = curl_easy_init();
    if (!handle) return 2;
    int values[] = {0};
    std::span<int> result(values);
    std::thread worker([&] { result[0] = curl_version_info(CURLVERSION_NOW)->version_num != 0; });
    worker.join();
    curl_easy_cleanup(handle);
    curl_global_cleanup();
    return result[0] == 1 ? 0 : 3;
}
