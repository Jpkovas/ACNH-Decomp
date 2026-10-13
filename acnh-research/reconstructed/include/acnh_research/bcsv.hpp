#pragma once
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>
namespace acnh_research {
struct Field { std::uint32_t key, offset, size; };
class BcsvView {
public:
    // Borrowed immutable storage: the caller keeps bytes alive for this view.
    explicit BcsvView(std::span<const std::uint8_t> bytes);
    std::uint32_t rows() const { return rows_; }
    std::uint32_t stride() const { return stride_; }
    std::span<const Field> fields() const { return fields_; }
    std::span<const std::uint8_t> field(std::uint32_t row, std::uint32_t key) const;
    std::uint32_t unsigned32(std::uint32_t row, std::uint32_t key) const;
private:
    std::span<const std::uint8_t> bytes_;
    std::vector<Field> fields_;
    std::size_t data_offset_{};
    std::uint32_t rows_{}, stride_{};
};
std::uint32_t crc32(std::span<const std::uint8_t> bytes);
}
