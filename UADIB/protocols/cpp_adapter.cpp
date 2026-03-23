// Optional C++ adapter skeleton for proprietary protocols.
// Build separately if required.

#include <string>

struct Packet {
    std::string payload;
};

class ProprietaryAdapter {
public:
    bool connect(const std::string& endpoint) {
        return !endpoint.empty();
    }

    Packet read_packet() {
        return Packet{"status=ok;"};
    }
};
