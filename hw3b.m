%% HW3-b
% Calculate the fundamental matrix using the normalized eight-point
% algorithm.
function ret = calculate_fundamental_matrix(pts1, pts2)
    %8 feature points between pts1 and pts2
    %Convert points to homogenous coordinates.
    [h,w] = size(pts1);
    hpts1 = [pts1 ones(h,1)];
    hpts2 = [pts2 ones(h,1)];
    
    % Normalize the two points
    [npts1,t1]= normalize_points(hpts1',2);
    [npts2,t2] = normalize_points(hpts2',2);
    
    % set up A
    A = zeros(8,9);
    
    for i = 1:8
        x = npts1(1,i);
        xp = npts2(1,i);
        y = npts1(2,i);
        yp = npts2(2,i);
        A(i,:) = [x*xp x*yp x y*xp y*yp y xp yp 1];
    end
    % f is eigenvector of A'.A corresponding to smallest eigenvalue. get
    % via SVD decomposition  --> Af = 0;
    [~,~,aV] = svd(A);
    % V = Eigenvector matrix of A'A

    % aVs is sorted in descending order, last element correspond to
    % smallest eigenvalue
    f = aV(:,end);
    %re-ordering F
    F = [f(1) f(2) f(3);f(4) f(5) f(6); f(7) f(8) f(9)]';
    [U,S,V] = svd(F);
    %modification of S
    min = S(1,1);
    idx = 0;
    for i = 1:3
        if S(i,i)<=min
            min = S(i,i);
            idx = i;
        end
    end
    S(idx,idx) = 0; %make smallest singular value zero
    F2 = U*S*V'; %reform Fundamental Matrix
    
    ret = t2' * F2 * t1; %normalized rescaling.
    
    
    %fmat ??


end