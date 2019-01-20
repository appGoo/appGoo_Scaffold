/*
agTxtWrap(textToWrap text, wrapStart text default = '{{{agWrap=', wrapEnd text default = '}}}')

return wrapStart || textToWrap || wrapEnd

This is just to give consistent output of wrapped text so that psql output can use the unique text identifier to ensure a particular value is returned