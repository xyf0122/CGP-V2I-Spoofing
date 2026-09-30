# Figure 7c-d. Match the author's original Figure 7a-b typography and dimensions.
library(ggplot2)
args <- commandArgs(trailingOnly=FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
root <- normalizePath(file.path(dirname(script), ".."))
d <- read.csv(file.path(root,"results","downsampling_metrics.csv"))
d$setting <- factor(ifelse(d$resolution_hz==10,"10 Hz","5 Hz"),levels=c("10 Hz","5 Hz"))
dir.create(file.path(root,"figures"),showWarnings=FALSE)
for (metric in c("MAE","MSE")) {
  plot_data <- data.frame(participant_id=d$participant_id,setting=d$setting,value=d[[metric]],metric=metric)
  ten <- plot_data[plot_data$setting=="10 Hz",];ten<-ten[order(ten$participant_id),]
  five <- plot_data[plot_data$setting=="5 Hz",];five<-five[order(five$participant_id),]
  test <- wilcox.test(ten$value,five$value,paired=TRUE)
  label <- if(test$p.value<.001) "***" else if(test$p.value<.01) "**" else if(test$p.value<.05) "*" else "ns"
  top <- max(plot_data$value)+diff(range(plot_data$value))*.08
  p <- ggplot(plot_data,aes(x=setting,y=value))+
    geom_line(aes(group=participant_id),color="grey45",alpha=.35,linewidth=.4)+
    geom_boxplot(aes(fill=setting),outlier.shape=NA,width=.55,staplewidth=.5,color="black",alpha=.85)+
    geom_point(shape=21,size=1.5,fill="white",color="black",stroke=.4,alpha=.85)+
    facet_wrap(~metric)+
    scale_fill_manual(values=c("10 Hz"="#2c7bb6","5 Hz"="#fdae61"))+
    labs(x=NULL,y=if(metric=="MAE") "MAE (mph)" else "MSE (mph\u00b2)")+
    theme_bw()+
    theme(text=element_text(family="Helvetica"),legend.position="none",
          strip.background=element_rect(colour="black",fill="black",linewidth=1),
          strip.text=element_text(colour="white",size=11,face="bold"),
          panel.border=element_rect(color="black",fill=NA,linewidth=1),
          axis.text=element_text(size=10,color="black"),axis.title=element_text(size=10,color="black"))+
    annotate("segment",x=1,xend=2,y=top,yend=top,linewidth=.3)+
    annotate("text",x=1.5,y=top,label=label,size=4,vjust=-.25,family="Helvetica")+
    scale_y_continuous(breaks=if(metric=="MAE") seq(0,15,5) else seq(0,200,50),expand=expansion(mult=c(.05,.20)))
  ggsave(file.path(root,"figures",paste0("FigR8_downsampling_paired_box_",metric,".pdf")),
         p,device=pdf,width=6.5,height=9,units="cm",family="Helvetica",useDingbats=FALSE)
}
cat("Figure 7c-d saved with the original Figure 7a-b font and label sizes.\n")
