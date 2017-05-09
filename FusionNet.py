from Basic_blocks import * 


class Conv_residual_conv(nn.Module):

    def __init__(self,in_dim,out_dim,act_fn):
        super(Conv_residual_conv,self).__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim
        act_fn = act_fn

        self.conv_1 = conv_block(self.in_dim,self.out_dim,act_fn)
        self.conv_2 = conv_block_3(self.out_dim,self.out_dim,act_fn)
        self.conv_3 = conv_block(self.out_dim,self.out_dim,act_fn)

    def forward(self,input):
        conv_1 = self.conv_1(input)
        conv_2 = self.conv_2(conv_1)
        res = conv_1 + conv_2
        conv_3 = self.conv_3(res)
        return conv_3


class FusionGenerator(nn.Module):

    def __init__(self,input_nc, output_nc, ngf, norm_layer):
        super(FusionGenerator,self).__init__()
        self.in_dim = input_nc
        self.out_dim = ngf
        self.final_out_dim = output_nc
        act_fn = nn.LeakyReLU(0.2, inplace=True)

        print("\n------Initiating FusionNet------\n")

        # encoder

        self.down_1 = nn.DataParallel(Conv_residual_conv(self.in_dim, self.out_dim, act_fn))
        self.pool_1 = nn.DataParallel(maxpool())
        self.down_2 = nn.DataParallel(Conv_residual_conv(self.out_dim, self.out_dim * 2, act_fn))
        self.pool_2 = nn.DataParallel(maxpool())
        self.down_3 = nn.DataParallel(Conv_residual_conv(self.out_dim * 2, self.out_dim * 4, act_fn))
        self.pool_3 = nn.DataParallel(maxpool())
        self.down_4 = nn.DataParallel(Conv_residual_conv(self.out_dim * 4, self.out_dim * 8, act_fn))
        self.pool_4 = nn.DataParallel(maxpool())

        # bridge

        self.bridge = nn.DataParallel(Conv_residual_conv(self.out_dim * 8, self.out_dim * 16, act_fn))

        # decoder

        self.deconv_1 = nn.DataParallel(conv_trans_block(self.out_dim * 16, self.out_dim * 8, act_fn))
        self.up_1 = nn.DataParallel(Conv_residual_conv(self.out_dim * 8, self.out_dim * 8, act_fn))
        self.deconv_2 = nn.DataParallel(conv_trans_block(self.out_dim * 8, self.out_dim * 4, act_fn))
        self.up_2 = nn.DataParallel(Conv_residual_conv(self.out_dim * 4, self.out_dim * 4, act_fn))
        self.deconv_3 = nn.DataParallel(conv_trans_block(self.out_dim * 4, self.out_dim * 2, act_fn))
        self.up_3 = nn.DataParallel(Conv_residual_conv(self.out_dim * 2, self.out_dim * 2, act_fn))
        self.deconv_4 = nn.DataParallel(conv_trans_block(self.out_dim * 2, self.out_dim, act_fn))
        self.up_4 = nn.DataParallel(Conv_residual_conv(self.out_dim, self.out_dim, act_fn))

        # output

        self.out = nn.DataParallel(nn.Conv2d(self.out_dim,self.final_out_dim, kernel_size=3, stride=1, padding=1))


    def forward(self,input):

        down_1 = self.down_1(input)
        pool_1 = self.pool_1(down_1)
        down_2 = self.down_2(pool_1)
        pool_2 = self.pool_2(down_2)
        down_3 = self.down_3(pool_2)
        pool_3 = self.pool_3(down_3)
        down_4 = self.down_4(pool_3)
        pool_4 = self.pool_4(down_4)

        bridge = self.bridge(pool_4)

        deconv_1 = self.deconv_1(bridge)
        skip_1 = deconv_1 + down_4
        up_1 = self.up_1(skip_1)
        deconv_2 = self.deconv_2(up_1)
        skip_2 = deconv_2 + down_3
        up_2 = self.up_2(skip_2)
        deconv_3 = self.deconv_3(up_2)
        skip_3 = deconv_3 + down_2
        up_3 = self.up_3(skip_3)
        deconv_4 = self.deconv_4(up_3)
        skip_4 = deconv_4 + down_1
        up_4 = self.up_4(skip_4)

        out = self.out(up_4)

        return out