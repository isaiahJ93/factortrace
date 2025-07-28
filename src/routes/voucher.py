@router.post("/generate")
async def create_voucher(input_data: VoucherInput):
    return generate_voucher(input_data)
